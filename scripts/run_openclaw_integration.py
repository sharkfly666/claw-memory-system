from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
import argparse
import json
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_api import AdminAPI
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.model_profiles_store import ModelProfilesStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OpenClaw workspace integration check for claw-memory-system.")
    parser.add_argument("--workspace", help="Workspace path to bootstrap and verify. Defaults to a temporary workspace.")
    parser.add_argument("--repo", default=str(ROOT), help="Repository root path. Defaults to the current repo.")
    parser.add_argument("--keep-workspace", action="store_true", help="Keep an auto-created temporary workspace after the run.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "output" / "playwright"),
        help="Directory for smoke screenshots and artifacts.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local smoke-test servers.")
    parser.add_argument("--api-port", type=int, default=8765, help="Admin HTTP port for the smoke test.")
    parser.add_argument("--frontend-port", type=int, default=18080, help="Static frontend port for the smoke test.")
    parser.add_argument("--browser-executable", default="", help="Optional browser executable path for the smoke test.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for the smoke-test servers and browser.")
    parser.add_argument("--headed", action="store_true", help="Launch the browser with a visible window during the smoke test.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip the browser smoke test and only run workspace integration checks.")
    return parser.parse_args()


def ensure_seed_memory(workspace: Path) -> Path:
    memory_md = workspace / "MEMORY.md"
    if not memory_md.exists():
        memory_md.write_text("# Primary model\nUse GPT-5 for the default assistant.\n")
    return memory_md


def run_checked(cmd: list[str], *, cwd: Path) -> dict[str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "command": cmd,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_wrapper_checks(workspace: Path) -> dict[str, dict[str, str]]:
    facts_wrapper = workspace / "memory-system" / "facts" / "facts_cli.py"
    build_wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
    search_wrapper = workspace / "memory-system" / "index" / "search_pageindex.py"

    facts_result = run_checked([sys.executable, str(facts_wrapper), "list"], cwd=workspace)
    build_result = run_checked([sys.executable, str(build_wrapper)], cwd=workspace)
    search_result = run_checked([sys.executable, str(search_wrapper), "primary model"], cwd=workspace)

    if not search_result["stdout"].strip():
        raise RuntimeError("Expected exact-search result to return at least one hit, got empty output")

    return {
        "facts_list": facts_result,
        "build_pageindex": build_result,
        "search_pageindex": search_result,
    }


def write_semantic_provider_fixture(path: Path) -> None:
    path.write_text(
        """import json
import sys

query = sys.argv[1]
limit = int(sys.argv[2])
provider = sys.argv[3]

print(json.dumps([
    {
        "entry": {
            "id": f"{provider}-fixture-1",
            "scope": "global",
            "category": "conversation",
            "text": f"{provider} fixture hit for {query}",
            "timestamp": "2026-03-13T00:00:00Z",
            "metadata": {
                "limit": limit,
                "provider": provider,
            },
        },
        "score": 0.93,
        "sources": {
            "semantic": 0.89,
        },
    }
]))
""",
        encoding="utf-8",
    )


def ensure_semantic_profile(workspace: Path) -> dict[str, object]:
    models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
    profiles = models.list("memory")
    if isinstance(profiles, list):
        enabled = [profile for profile in profiles if profile.get("enabled", True)]
        if enabled:
            selected = next((profile for profile in enabled if profile.get("active")), enabled[0])
            return {
                "seeded": False,
                "profile_name": selected.get("name"),
                "provider": selected.get("provider"),
            }

    fixture_path = workspace / "memory-system" / "semantic_provider_fixture.py"
    write_semantic_provider_fixture(fixture_path)
    models.upsert(
        "memory",
        "default",
        {
            "provider": "memory-lancedb-pro",
            "enabled": True,
            "active": True,
            "command": [sys.executable, str(fixture_path), "{query}", "{limit}", "memory-lancedb-pro"],
        },
    )
    return {
        "seeded": True,
        "profile_name": "default",
        "provider": "memory-lancedb-pro",
        "fixture_path": str(fixture_path),
    }


def run_semantic_checks(workspace: Path) -> dict[str, object]:
    profile = ensure_semantic_profile(workspace)
    api = AdminAPI.from_workspace(workspace)
    if not api.semantic_adapter:
        raise RuntimeError("Expected semantic adapter to be configured after semantic profile setup")
    result = api.inspect_query("semantic memory integration")
    if result["layer_hits"].get("vector", 0) < 1:
        raise RuntimeError(f"Expected semantic adapter inspection to return vector hits, got: {json.dumps(result, ensure_ascii=False)}")
    return {
        "seeded": profile["seeded"],
        "profile_name": profile["profile_name"],
        "provider": api.semantic_adapter.provider,
        "result": result,
    }


def run_repo_smoke(
    *,
    workspace: Path,
    output_dir: Path,
    host: str,
    api_port: int,
    frontend_port: int,
    browser_executable: str,
    timeout: float,
    headed: bool,
) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_webapp_smoke.py"),
        "--workspace",
        str(workspace),
        "--host",
        host,
        "--api-port",
        str(api_port),
        "--frontend-port",
        str(frontend_port),
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(timeout),
    ]
    if browser_executable:
        cmd.extend(["--browser-executable", browser_executable])
    if headed:
        cmd.append("--headed")

    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "command": cmd,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return json.loads(result.stdout)


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    temp_root: Path | None = None
    auto_workspace = False
    try:
        if args.workspace:
            workspace = Path(args.workspace).expanduser().resolve()
            workspace.mkdir(parents=True, exist_ok=True)
        else:
            temp_root = Path(mkdtemp(prefix="openclaw-integration-"))
            workspace = temp_root / "workspace"
            auto_workspace = True

        bootstrap(workspace, repo)
        memory_md = ensure_seed_memory(workspace)
        wrapper_checks = run_wrapper_checks(workspace)
        semantic_checks = run_semantic_checks(workspace)
        if args.skip_smoke:
            smoke = {"skipped": True}
        else:
            smoke = run_repo_smoke(
                workspace=workspace,
                output_dir=output_dir,
                host=args.host,
                api_port=args.api_port,
                frontend_port=args.frontend_port,
                browser_executable=args.browser_executable,
                timeout=args.timeout,
                headed=args.headed,
            )

        result = {
            "ok": True,
            "repo": str(repo),
            "workspace": str(workspace),
            "seed_memory": str(memory_md),
            "wrapper_checks": wrapper_checks,
            "semantic_checks": semantic_checks,
            "smoke": smoke,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        if temp_root is not None and auto_workspace and not args.keep_workspace:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
