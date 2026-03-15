from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_api import AdminAPI
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.memory_governance import MemoryGovernance


class MemoryGovernanceTest(unittest.TestCase):
    def test_build_report_flags_empty_layers_and_candidates_from_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text(
                "用户偏好：直接高效，少废话。\n待办：继续优化 daily-briefing。\n问题：之前因 timeout 做过修复。\n",
                encoding="utf-8",
            )

            report = MemoryGovernance.from_workspace(workspace).build_report()

            self.assertIn("preferences", report["empty_layers"])
            self.assertIn("tasks", report["empty_layers"])
            self.assertIn("episodes", report["empty_layers"])
            self.assertGreaterEqual(report["summary"]["migration_candidate_count"], 3)
            layers = {item["suggested_layer"] for item in report["migration_candidates"]}
            self.assertIn("preferences", layers)
            self.assertIn("tasks", layers)
            self.assertIn("episodes", layers)

    def test_build_report_detects_multiple_active_preferences_same_stem(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)
            api.preferences.upsert(
                "user.communication_style",
                {
                    "summary": "直接高效",
                    "aliases": ["少废话"],
                    "tags": ["communication"],
                    "status": "active",
                },
            )
            api.preferences.upsert(
                "user.communication_style_alt",
                {
                    "summary": "直接一点",
                    "aliases": ["高效沟通"],
                    "tags": ["communication"],
                    "status": "active",
                },
            )

            report = MemoryGovernance.from_workspace(workspace).build_report()
            conflict_types = [item["type"] for item in report["issues"]["conflicts"]]
            self.assertIn("multiple_active_preferences", conflict_types)

    def test_admin_api_can_write_governance_report_file(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            payload = api.write_governance_report_response()

            self.assertTrue(payload["ok"])
            path = Path(payload["data"]["path"])
            self.assertTrue(path.exists())
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "memory-governance-report.v1")


if __name__ == "__main__":
    unittest.main()
