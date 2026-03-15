from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import stat
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.bootstrap_openclaw_instance import bootstrap


def write_openclaw_config(path: Path, *, memory_slot: str, session_memory_enabled: bool = True) -> None:
    payload = {
        "agents": {
            "defaults": {
                "workspace": str(path.parent / "workspace"),
            }
        },
        "hooks": {
            "internal": {
                "enabled": True,
                "entries": {
                    "session-memory": {
                        "enabled": session_memory_enabled,
                    }
                },
            }
        },
        "plugins": {
            "enabled": True,
            "allow": ["memory-lancedb-pro", "memos-local-openclaw-plugin"],
            "load": {
                "paths": [
                    str(path.parent / "workspace" / "plugins" / "memory-lancedb-pro"),
                ]
            },
            "slots": {
                "memory": memory_slot,
            },
            "entries": {
                "memory-lancedb-pro": {
                    "enabled": True,
                    "config": {
                        "autoRecall": False,
                    },
                }
            },
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_fake_openclaw(
    path: Path,
    *,
    memory_pro_available: bool,
    version: str = "1.0.20",
    legacy_database_found: bool = False,
    migration_needed: bool = False,
    dry_run_count: int = 3,
) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
if args[:2] == ["memory-pro", "version"]:
    if {str(memory_pro_available)}:
        print("[plugins] memory-lancedb-pro: plugin registered")
        print("{version}")
        print("[plugins] memory-lancedb-pro: diagnostic build tag loaded")
        raise SystemExit(0)
    print("error: unknown command 'memory-pro'", file=sys.stderr)
    raise SystemExit(1)

if args[:3] == ["memory-pro", "migrate", "check"]:
    print("[plugins] memory-lancedb-pro: plugin registered")
    print("Migration Check Results:")
    print("• Legacy database found: {'Yes' if legacy_database_found else 'No'}")
    print("• Migration needed: {'Yes' if migration_needed else 'No'}")
    raise SystemExit(0)

if len(args) >= 3 and args[:2] == ["memory-pro", "import"] and "--dry-run" in args:
    import_file = pathlib.Path(args[2])
    payload = json.loads(import_file.read_text(encoding="utf-8"))
    print("[plugins] memory-lancedb-pro: plugin registered")
    print("DRY RUN - No memories will be imported")
    print(f"Would import {dry_run_count} memories")
    print("Target scope: global")
    raise SystemExit(0)

print("unsupported command", args, file=sys.stderr)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def seed_workspace(workspace: Path) -> None:
    bootstrap(workspace, ROOT)
    (workspace / "MEMORY.md").write_text(
        "# MEMORY.md\n- **Primary model**: GPT-5\n- **发送时间**: 每天早上 8:00\n",
        encoding="utf-8",
    )
    memory_dir = workspace / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "2026-03-13.md").write_text(
        "- Session Key: agent:main:main\n- 状态: ✅ 已完成 Beta 收口\n",
        encoding="utf-8",
    )
    plugin_dir = workspace / "plugins" / "memory-lancedb-pro"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "openclaw.plugin.json").write_text(
        json.dumps({"id": "memory-lancedb-pro", "kind": "memory"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class OpenClawDeepIntegrationScriptTest(unittest.TestCase):
    def test_script_exposes_expected_cli_options(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--openclaw-home", result.stdout)
        self.assertIn("--openclaw-bin", result.stdout)
        self.assertIn("--strict", result.stdout)

    def test_script_reports_ready_runtime_and_migration_checks(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            openclaw_home = base / ".openclaw"
            workspace = openclaw_home / "workspace"
            openclaw_home.mkdir(parents=True, exist_ok=True)
            seed_workspace(workspace)
            write_openclaw_config(openclaw_home / "openclaw.json", memory_slot="memory-lancedb-pro", session_memory_enabled=False)
            fake_openclaw = base / "openclaw"
            write_fake_openclaw(fake_openclaw, memory_pro_available=True)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo",
                    str(ROOT),
                    "--openclaw-home",
                    str(openclaw_home),
                    "--openclaw-bin",
                    str(fake_openclaw),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["openclaw"]["memory_slot"], "memory-lancedb-pro")
        self.assertFalse(payload["openclaw"]["session_memory_hook_enabled"])
        self.assertTrue(payload["openclaw"]["memory_pro_available"])
        self.assertEqual(payload["openclaw"]["memory_pro_version"], "1.0.20")
        self.assertGreaterEqual(payload["migration_checks"]["fact_candidates"]["count"], 2)
        self.assertEqual(payload["migration_checks"]["import_mode"], "dry_run")
        self.assertFalse(payload["migration_checks"]["actual_import_performed"])
        self.assertTrue(payload["migration_checks"]["memory_pro_migrate_check"]["ok"])
        self.assertFalse(payload["migration_checks"]["memory_pro_migrate_check"]["legacy_database_found"])
        self.assertFalse(payload["migration_checks"]["memory_pro_migrate_check"]["migration_needed"])
        self.assertTrue(payload["migration_checks"]["memory_pro_import_dry_run"]["ok"])
        self.assertEqual(payload["migration_checks"]["memory_pro_import_dry_run"]["planned_import_count"], 3)

    def test_script_parses_noisy_migration_cli_output(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            openclaw_home = base / ".openclaw"
            workspace = openclaw_home / "workspace"
            openclaw_home.mkdir(parents=True, exist_ok=True)
            seed_workspace(workspace)
            write_openclaw_config(openclaw_home / "openclaw.json", memory_slot="memory-lancedb-pro", session_memory_enabled=False)
            fake_openclaw = base / "openclaw"
            write_fake_openclaw(
                fake_openclaw,
                memory_pro_available=True,
                version="1.1.0-beta.8",
                legacy_database_found=True,
                migration_needed=True,
                dry_run_count=7,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo",
                    str(ROOT),
                    "--openclaw-home",
                    str(openclaw_home),
                    "--openclaw-bin",
                    str(fake_openclaw),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["openclaw"]["memory_pro_version"], "1.1.0-beta.8")
        self.assertTrue(payload["migration_checks"]["memory_pro_migrate_check"]["legacy_database_found"])
        self.assertTrue(payload["migration_checks"]["memory_pro_migrate_check"]["migration_needed"])
        self.assertEqual(payload["migration_checks"]["memory_pro_import_dry_run"]["planned_import_count"], 7)

    def test_script_falls_back_to_repo_migration_and_index_tools_when_workspace_wrappers_are_broken(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            openclaw_home = base / ".openclaw"
            workspace = openclaw_home / "workspace"
            openclaw_home.mkdir(parents=True, exist_ok=True)
            seed_workspace(workspace)
            write_openclaw_config(openclaw_home / "openclaw.json", memory_slot="memory-lancedb-pro", session_memory_enabled=False)
            fake_openclaw = base / "openclaw"
            write_fake_openclaw(fake_openclaw, memory_pro_available=True)

            broken_build = workspace / "memory-system" / "index" / "build_pageindex.py"
            broken_extract = workspace / "memory-system" / "migrations" / "extract_fact_candidates.py"
            broken_build.write_text("raise SystemExit(1)\n", encoding="utf-8")
            broken_extract.write_text("raise SystemExit(1)\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo",
                    str(ROOT),
                    "--openclaw-home",
                    str(openclaw_home),
                    "--openclaw-bin",
                    str(fake_openclaw),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready"])
        self.assertTrue(payload["wrapper_checks"]["build_pageindex"]["ok"])
        self.assertGreaterEqual(payload["migration_checks"]["fact_candidates"]["count"], 2)

    def test_script_reports_not_ready_when_memory_slot_mismatches(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            openclaw_home = base / ".openclaw"
            workspace = openclaw_home / "workspace"
            openclaw_home.mkdir(parents=True, exist_ok=True)
            seed_workspace(workspace)
            write_openclaw_config(openclaw_home / "openclaw.json", memory_slot="memos-local-openclaw-plugin")
            fake_openclaw = base / "openclaw"
            write_fake_openclaw(fake_openclaw, memory_pro_available=False)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo",
                    str(ROOT),
                    "--openclaw-home",
                    str(openclaw_home),
                    "--openclaw-bin",
                    str(fake_openclaw),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["openclaw"]["memory_slot"], "memos-local-openclaw-plugin")
        self.assertFalse(payload["openclaw"]["memory_pro_available"])
        self.assertTrue(any("memory slot" in issue.lower() for issue in payload["issues"]))

    def test_script_strict_mode_fails_when_runtime_is_not_ready(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_deep_integration.py"
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            openclaw_home = base / ".openclaw"
            workspace = openclaw_home / "workspace"
            openclaw_home.mkdir(parents=True, exist_ok=True)
            seed_workspace(workspace)
            write_openclaw_config(openclaw_home / "openclaw.json", memory_slot="memos-local-openclaw-plugin")
            fake_openclaw = base / "openclaw"
            write_fake_openclaw(fake_openclaw, memory_pro_available=False)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo",
                    str(ROOT),
                    "--openclaw-home",
                    str(openclaw_home),
                    "--openclaw-bin",
                    str(fake_openclaw),
                    "--strict",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ready"])


if __name__ == "__main__":
    unittest.main()
