from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import json
import os
import re
import subprocess
import sys


def load_openclaw_config(openclaw_home: Path) -> dict[str, Any]:
    config_path = openclaw_home / "openclaw.json"
    if not config_path.exists():
        raise FileNotFoundError(f"OpenClaw config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def resolve_workspace(openclaw_home: Path, config: dict[str, Any], workspace: Path | None = None) -> Path:
    if workspace is not None:
        return workspace.expanduser().resolve()
    configured = (
        config.get("agents", {})
        .get("defaults", {})
        .get("workspace")
    )
    if configured:
        return Path(str(configured)).expanduser().resolve()
    return (openclaw_home / "workspace").resolve()


def inspect_openclaw_state(openclaw_home: Path, workspace: Path, config: dict[str, Any]) -> dict[str, Any]:
    plugins = config.get("plugins", {})
    hooks = config.get("hooks", {})
    allow = plugins.get("allow", [])
    load_paths = plugins.get("load", {}).get("paths", [])
    entries = plugins.get("entries", {})
    memory_slot = plugins.get("slots", {}).get("memory")
    plugin_dir = workspace / "plugins" / "memory-lancedb-pro"
    return {
        "home": str(openclaw_home),
        "workspace": str(workspace),
        "memory_slot": memory_slot,
        "plugin_allowed": "memory-lancedb-pro" in allow if isinstance(allow, list) else False,
        "load_paths": load_paths,
        "plugin_directory": str(plugin_dir),
        "plugin_directory_exists": plugin_dir.exists(),
        "plugin_entry_enabled": bool(entries.get("memory-lancedb-pro", {}).get("enabled")),
        "session_memory_hook_enabled": bool(
            hooks.get("internal", {})
            .get("entries", {})
            .get("session-memory", {})
            .get("enabled")
        ),
    }


def run_command(cmd: list[str], *, cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }


def _repo_env(repo: Path) -> dict[str, str]:
    env = dict(**os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(repo / "src") + (f"{os.pathsep}{existing}" if existing else "")
    return env


def run_command_with_env(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }


def run_wrapper_checks(workspace: Path, query: str, *, repo: Path, artifacts_dir: Path) -> dict[str, Any]:
    facts_wrapper = workspace / "memory-system" / "facts" / "facts_cli.py"
    build_wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
    search_wrapper = workspace / "memory-system" / "index" / "search_pageindex.py"
    facts_result = run_command([sys.executable, str(facts_wrapper), "list"], cwd=workspace)
    build_result = run_command([sys.executable, str(build_wrapper)], cwd=workspace)
    db_path = workspace / "memory-system" / "index" / "pageindex.sqlite"
    build_used_fallback = False
    search_used_fallback = False

    if not build_result["ok"]:
        build_used_fallback = True
        db_path = artifacts_dir / "pageindex.sqlite"
        build_result = run_command_with_env(
            [
                sys.executable,
                "-m",
                "claw_memory_system.build_pageindex",
                "--root",
                str(workspace),
                "--db",
                str(db_path),
                "--facts",
                str(workspace / "memory-system" / "facts" / "facts.json"),
                "--schema",
                str(repo / "sql" / "pageindex_schema.sql"),
            ],
            cwd=repo,
            env=_repo_env(repo),
        )

    search_result = run_command([sys.executable, str(search_wrapper), query], cwd=workspace)
    if not search_result["ok"] or (build_used_fallback and not search_result["stdout"].strip()):
        search_used_fallback = True
        search_result = run_command_with_env(
            [
                sys.executable,
                "-m",
                "claw_memory_system.search_pageindex",
                "--db",
                str(db_path),
                query,
            ],
            cwd=repo,
            env=_repo_env(repo),
        )
    return {
        "query": query,
        "facts_list": facts_result,
        "build_pageindex": build_result,
        "search_pageindex": search_result,
        "build_used_fallback": build_used_fallback,
        "search_used_fallback": search_used_fallback,
    }


def extract_fact_candidates(workspace: Path, repo: Path, artifacts_dir: Path) -> dict[str, Any]:
    wrapper = workspace / "memory-system" / "migrations" / "extract_fact_candidates.py"
    extractor = wrapper if wrapper.exists() else repo / "src" / "claw_memory_system" / "extract_fact_candidates.py"
    out_path = artifacts_dir / "fact-candidates.jsonl"
    result = run_command(
        [
            sys.executable,
            str(extractor),
            "--root",
            str(workspace),
            "--out",
            str(out_path),
        ],
        cwd=workspace,
    )
    candidates: list[dict[str, Any]] = []
    if out_path.exists():
        with out_path.open(encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    candidates.append(json.loads(text))
    used_fallback = False
    if (not result["ok"] or not candidates) and wrapper.exists():
        used_fallback = True
        out_path = artifacts_dir / "fact-candidates-fallback.jsonl"
        result = run_command_with_env(
            [
                sys.executable,
                str(repo / "src" / "claw_memory_system" / "extract_fact_candidates.py"),
                "--root",
                str(workspace),
                "--out",
                str(out_path),
            ],
            cwd=repo,
            env=_repo_env(repo),
        )
        candidates = []
        if out_path.exists():
            with out_path.open(encoding="utf-8") as handle:
                for line in handle:
                    text = line.strip()
                    if text:
                        candidates.append(json.loads(text))
    return {
        "ok": result["ok"],
        "command": result["command"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "output": str(out_path),
        "count": len(candidates),
        "sample": candidates[:5],
        "candidates": candidates,
        "used_fallback": used_fallback,
    }


def choose_search_query(candidates: list[dict[str, Any]]) -> str:
    for candidate in candidates[:10]:
        for key in ("candidate_key", "candidate_value"):
            value = str(candidate.get(key, "")).strip("` ").strip()
            if value:
                return value
    return "memory"


def probe_memory_pro(openclaw_bin: str, workspace: Path) -> dict[str, Any]:
    result = run_command([openclaw_bin, "memory-pro", "version"], cwd=workspace)
    version = ""
    if result["ok"]:
        matches = re.findall(r"(?m)^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$", result["stdout"])
        version = matches[-1] if matches else result["stdout"].strip()
    return {
        "ok": result["ok"],
        "available": result["ok"],
        "version": version,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "command": result["command"],
    }


def _parse_yes_no_field(stdout: str, label: str) -> bool | None:
    match = re.search(rf"{re.escape(label)}:\s*(Yes|No)\b", stdout, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "yes"


def _parse_would_import_count(stdout: str) -> int | None:
    match = re.search(r"Would import\s+(\d+)\s+memories\b", stdout, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def build_memory_import_file(candidates: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    memories = []
    for candidate in candidates[:3]:
        key = str(candidate.get("candidate_key", "")).strip()
        value = str(candidate.get("candidate_value", "")).strip()
        if not key or not value:
            continue
        memories.append(
            {
                "text": f"{key}: {value}",
                "category": "fact",
                "importance": float(candidate.get("confidence", 0.7) or 0.7),
                "metadata": {
                    "source": candidate.get("source"),
                    "line": candidate.get("line"),
                    "migration_test": True,
                },
            }
        )
    payload = {"memories": memories}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def run_memory_pro_migration_checks(
    openclaw_bin: str,
    workspace: Path,
    candidates: list[dict[str, Any]],
    artifacts_dir: Path,
) -> dict[str, Any]:
    availability = probe_memory_pro(openclaw_bin, workspace)
    if not availability["available"]:
        return {
            "available": False,
            "version": "",
            "import_mode": "unavailable",
            "actual_import_performed": False,
            "memory_pro_migrate_check": {
                "ok": False,
                "skipped": True,
                "reason": "memory-pro CLI unavailable",
                "legacy_database_found": None,
                "migration_needed": None,
            },
            "memory_pro_import_dry_run": {
                "ok": False,
                "skipped": True,
                "reason": "memory-pro CLI unavailable",
                "planned_import_count": None,
            },
        }

    import_file = artifacts_dir / "memory-import-dry-run.json"
    payload = build_memory_import_file(candidates, import_file)
    migrate_check_raw = run_command([openclaw_bin, "memory-pro", "migrate", "check"], cwd=workspace)
    migrate_check = {
        **migrate_check_raw,
        "legacy_database_found": _parse_yes_no_field(migrate_check_raw["stdout"], "Legacy database found"),
        "migration_needed": _parse_yes_no_field(migrate_check_raw["stdout"], "Migration needed"),
    }
    import_dry_run_raw = run_command(
        [openclaw_bin, "memory-pro", "import", str(import_file), "--scope", "global", "--dry-run"],
        cwd=workspace,
    )
    import_dry_run = {
        **import_dry_run_raw,
        "planned_import_count": _parse_would_import_count(import_dry_run_raw["stdout"]),
    }
    return {
        "available": True,
        "version": availability["version"],
        "import_mode": "dry_run",
        "actual_import_performed": False,
        "import_payload_count": len(payload.get("memories", [])),
        "memory_pro_migrate_check": migrate_check,
        "memory_pro_import_dry_run": import_dry_run,
    }


def run_deep_integration(
    *,
    repo: Path,
    openclaw_home: Path,
    openclaw_bin: str,
    workspace: Path | None = None,
) -> dict[str, Any]:
    config = load_openclaw_config(openclaw_home)
    resolved_workspace = resolve_workspace(openclaw_home, config, workspace)
    openclaw_state = inspect_openclaw_state(openclaw_home, resolved_workspace, config)

    with TemporaryDirectory(prefix="openclaw-deep-integration-") as tmp:
        artifacts_dir = Path(tmp)
        fact_candidates = extract_fact_candidates(resolved_workspace, repo, artifacts_dir)
        search_query = choose_search_query(fact_candidates["candidates"])
        wrapper_checks = run_wrapper_checks(resolved_workspace, search_query, repo=repo, artifacts_dir=artifacts_dir)
        migration_checks = run_memory_pro_migration_checks(
            openclaw_bin,
            resolved_workspace,
            fact_candidates["candidates"],
            artifacts_dir,
        )

    issues: list[str] = []
    if openclaw_state["memory_slot"] != "memory-lancedb-pro":
        issues.append(f"Active memory slot is {openclaw_state['memory_slot']!r}, expected 'memory-lancedb-pro'.")
    if not openclaw_state["plugin_directory_exists"]:
        issues.append("memory-lancedb-pro plugin directory is missing from the workspace plugins directory.")
    if not openclaw_state["plugin_allowed"]:
        issues.append("memory-lancedb-pro is not present in plugins.allow.")
    if fact_candidates["count"] == 0:
        issues.append("No legacy fact candidates were extracted from MEMORY.md / memory/*.md.")
    if not wrapper_checks["facts_list"]["ok"]:
        issues.append("facts_cli wrapper failed.")
    if not wrapper_checks["build_pageindex"]["ok"]:
        issues.append("build_pageindex wrapper failed.")
    if not wrapper_checks["search_pageindex"]["ok"]:
        issues.append("search_pageindex wrapper failed.")
    if not migration_checks["available"]:
        issues.append("openclaw memory-pro CLI is unavailable in the current runtime.")
    else:
        if not migration_checks["memory_pro_migrate_check"]["ok"]:
            issues.append("openclaw memory-pro migrate check failed.")
        if not migration_checks["memory_pro_import_dry_run"]["ok"]:
            issues.append("openclaw memory-pro import --dry-run failed.")

    return {
        "ok": True,
        "ready": not issues,
        "openclaw": {
            **openclaw_state,
            "memory_pro_available": migration_checks["available"],
            "memory_pro_version": migration_checks["version"],
        },
        "wrapper_checks": wrapper_checks,
        "migration_checks": {
            "fact_candidates": {
                "count": fact_candidates["count"],
                "sample": fact_candidates["sample"],
                "output": fact_candidates["output"],
                "ok": fact_candidates["ok"],
                "used_fallback": fact_candidates["used_fallback"],
            },
            "import_mode": migration_checks["import_mode"],
            "actual_import_performed": migration_checks["actual_import_performed"],
            "memory_pro_migrate_check": migration_checks["memory_pro_migrate_check"],
            "memory_pro_import_dry_run": migration_checks["memory_pro_import_dry_run"],
        },
        "issues": issues,
    }
