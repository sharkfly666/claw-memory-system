from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OpenClawIntegrationScriptTest(unittest.TestCase):
    def test_run_openclaw_integration_script_exposes_expected_cli_options(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_integration.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--workspace", result.stdout)
        self.assertIn("--repo", result.stdout)
        self.assertIn("--keep-workspace", result.stdout)
        self.assertIn("--browser-executable", result.stdout)
        self.assertIn("--output-dir", result.stdout)
        self.assertIn("--skip-smoke", result.stdout)

    def test_run_openclaw_integration_script_reports_semantic_checks_without_smoke(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_integration.py"
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace",
                    str(workspace),
                    "--repo",
                    str(ROOT),
                    "--skip-smoke",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["semantic_checks"]["provider"], "memory-lancedb-pro")
        self.assertGreaterEqual(payload["semantic_checks"]["result"]["layer_hits"].get("vector", 0), 1)

    def test_run_openclaw_integration_script_accepts_facts_only_exact_search_hit(self) -> None:
        script = ROOT / "scripts" / "run_openclaw_integration.py"
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            facts_dir = workspace / "memory-system" / "facts"
            facts_dir.mkdir(parents=True, exist_ok=True)
            (workspace / "MEMORY.md").write_text("# Workspace note\nNo model alias here.\n")
            (facts_dir / "facts.json").write_text(
                json.dumps(
                    {
                        "version": "1.0",
                        "facts": {
                            "agent.primary_model": {
                                "value": "gongyi1/gpt-5.4",
                                "value_type": "string",
                                "category": "fact",
                                "status": "active",
                                "updated_at": "2026-03-13T00:00:00+08:00",
                                "created_at": "2026-03-13T00:00:00+08:00",
                                "last_verified": "2026-03-13T00:00:00+08:00",
                                "valid_from": "2026-03-13T00:00:00+08:00",
                                "valid_to": None,
                                "ttl_days": None,
                                "confidence": 1.0,
                                "source": "test",
                                "scope": "global",
                                "aliases": ["primary model"],
                                "tags": ["agent", "model"],
                                "notes": "Configured in agents.defaults.model.primary.",
                                "superseded_by": None,
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace",
                    str(workspace),
                    "--repo",
                    str(ROOT),
                    "--skip-smoke",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertIn("fact:agent.primary_model", payload["wrapper_checks"]["search_pageindex"]["stdout"])


if __name__ == "__main__":
    unittest.main()
