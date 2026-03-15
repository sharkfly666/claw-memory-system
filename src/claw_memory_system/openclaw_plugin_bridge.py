from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = Path("~/.openclaw/workspace").expanduser()
DEFAULT_OPENCLAW_HOME = Path("~/.openclaw").expanduser()


@dataclass(frozen=True)
class ToolSpec:
    description: str


@dataclass(frozen=True)
class BridgeCommand:
    argv: list[str]
    cwd: Path
    env: dict[str, str]


TOOL_SPECS: dict[str, ToolSpec] = {
    "claw_memory_bootstrap": ToolSpec(
        description="Bootstrap claw-memory-system runtime files into an OpenClaw workspace.",
    ),
    "claw_memory_build_index": ToolSpec(
        description="Build the exact-search page index for the current OpenClaw workspace.",
    ),
    "claw_memory_search_index": ToolSpec(
        description="Search the exact-search page index for a query string.",
    ),
    "claw_memory_facts_list": ToolSpec(
        description="List facts stored in the OpenClaw workspace runtime.",
    ),
    "claw_memory_facts_get": ToolSpec(
        description="Get one fact record by key from the OpenClaw workspace runtime.",
    ),
    "claw_memory_integration_check": ToolSpec(
        description="Run the repo-owned OpenClaw integration check, defaulting to skip browser smoke.",
    ),
    "claw_memory_deep_integration_check": ToolSpec(
        description="Run the repo-owned deep OpenClaw integration and migration checks.",
    ),
    "claw_memory_batch_governance": ToolSpec(
        description="Run the batch governance workflow for structured memory candidates and reports.",
    ),
    "claw_memory_classify_turn": ToolSpec(
        description="Classify a turn for autonomous memory handling decisions.",
    ),
    "claw_memory_queue_turn_candidates": ToolSpec(
        description="Classify a turn and queue portable pending memory candidates.",
    ),
}


def _runtime_facts_path(workspace: Path) -> Path:
    return workspace / "memory-system" / "facts" / "facts.json"


def _runtime_index_db_path(workspace: Path) -> Path:
    return workspace / "memory-system" / "index" / "pageindex.sqlite"


def _repo_env(repo: Path) -> dict[str, str]:
    return {"PYTHONPATH": str(repo / "src")}


def build_bridge_command(
    tool_name: str,
    *,
    repo: Path,
    workspace: Path | None = None,
    openclaw_home: Path | None = None,
    openclaw_bin: str = "openclaw",
    python_bin: str = "python3",
    query: str | None = None,
    key: str | None = None,
    user_text: str | None = None,
    assistant_text: str | None = None,
    tool_summary: str | None = None,
    skip_smoke: bool = True,
    strict: bool = False,
) -> BridgeCommand:
    repo = Path(repo).expanduser().resolve()
    resolved_workspace = Path(workspace).expanduser() if workspace else DEFAULT_WORKSPACE
    resolved_openclaw_home = Path(openclaw_home).expanduser() if openclaw_home else DEFAULT_OPENCLAW_HOME
    env = _repo_env(repo)

    if tool_name == "claw_memory_bootstrap":
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.bootstrap_openclaw_instance",
            "--workspace",
            str(resolved_workspace),
            "--repo",
            str(repo),
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_build_index":
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.build_pageindex",
            "--root",
            str(resolved_workspace),
            "--db",
            str(_runtime_index_db_path(resolved_workspace)),
            "--facts",
            str(_runtime_facts_path(resolved_workspace)),
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_search_index":
        if not query:
            raise ValueError("query is required for claw_memory_search_index")
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.search_pageindex",
            "--db",
            str(_runtime_index_db_path(resolved_workspace)),
            query,
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_facts_list":
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.facts_cli",
            "--facts",
            str(_runtime_facts_path(resolved_workspace)),
            "list",
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_facts_get":
        if not key:
            raise ValueError("key is required for claw_memory_facts_get")
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.facts_cli",
            "--facts",
            str(_runtime_facts_path(resolved_workspace)),
            "get",
            key,
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_integration_check":
        argv = [
            python_bin,
            str(repo / "scripts" / "run_openclaw_integration.py"),
            "--workspace",
            str(resolved_workspace),
            "--repo",
            str(repo),
        ]
        if skip_smoke:
            argv.append("--skip-smoke")
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_deep_integration_check":
        argv = [
            python_bin,
            str(repo / "scripts" / "run_openclaw_deep_integration.py"),
            "--repo",
            str(repo),
            "--openclaw-home",
            str(resolved_openclaw_home),
            "--openclaw-bin",
            openclaw_bin,
        ]
        if workspace:
            argv.extend(["--workspace", str(resolved_workspace)])
        if strict:
            argv.append("--strict")
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_batch_governance":
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.batch_governance_cli",
            "--workspace",
            str(resolved_workspace),
            "--write",
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_classify_turn":
        user_text = query or ""
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.post_turn_classifier_cli",
            "--workspace",
            str(resolved_workspace),
            "--user-text",
            user_text,
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    if tool_name == "claw_memory_queue_turn_candidates":
        argv = [
            python_bin,
            "-m",
            "claw_memory_system.turn_candidate_bridge_cli",
            "--workspace",
            str(resolved_workspace),
            "--user-text",
            user_text or query or "",
            "--assistant-text",
            assistant_text or "",
            "--tool-summary",
            tool_summary or "",
            "--min-confidence",
            "0.88",
        ]
        return BridgeCommand(argv=argv, cwd=repo, env=env)

    raise ValueError(f"Unsupported tool_name: {tool_name}")


def run_bridge_command(command: BridgeCommand) -> dict[str, object]:
    env = dict(os.environ)
    env.update(command.env)
    result = subprocess.run(
        command.argv,
        cwd=str(command.cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    payload: dict[str, object] = {
        "command": command.argv,
        "cwd": str(command.cwd),
        "env": command.env,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload["parsed_stdout"] = json.loads(stdout)
        except json.JSONDecodeError:
            payload["parsed_stdout"] = None
    else:
        payload["parsed_stdout"] = None
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bridge OpenClaw plugin tools to the repo-owned Python runtime.")
    parser.add_argument("tool", choices=sorted(TOOL_SPECS))
    parser.add_argument("--repo", default=str(ROOT), help="Repository root path. Defaults to the current repo.")
    parser.add_argument("--workspace", help="OpenClaw workspace path. Defaults to ~/.openclaw/workspace.")
    parser.add_argument("--openclaw-home", help="OpenClaw home path. Defaults to ~/.openclaw.")
    parser.add_argument("--openclaw-bin", default="openclaw", help="OpenClaw executable to use.")
    parser.add_argument("--python-bin", default="python3", help="Python executable to use for downstream commands.")
    parser.add_argument("--query", help="Query value for exact-search actions.")
    parser.add_argument("--key", help="Fact key for facts-get actions.")
    parser.add_argument("--user-text", help="User text for turn-classification actions.")
    parser.add_argument("--assistant-text", help="Assistant text for turn-classification actions.")
    parser.add_argument("--tool-summary", help="Tool summary text for turn-classification actions.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip browser smoke when running integration check.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when readiness checks fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        command = build_bridge_command(
            args.tool,
            repo=Path(args.repo),
            workspace=Path(args.workspace) if args.workspace else None,
            openclaw_home=Path(args.openclaw_home) if args.openclaw_home else None,
            openclaw_bin=args.openclaw_bin,
            python_bin=args.python_bin,
            query=args.query,
            key=args.key,
            user_text=args.user_text,
            assistant_text=args.assistant_text,
            tool_summary=args.tool_summary,
            skip_smoke=args.skip_smoke,
            strict=args.strict,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload = run_bridge_command(command)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return int(payload["returncode"])


if __name__ == "__main__":
    raise SystemExit(main())
