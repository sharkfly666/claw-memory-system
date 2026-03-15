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
from claw_memory_system.memory_migrator import MemoryMigrator


class MemoryMigratorTest(unittest.TestCase):
    def test_bootstrap_core_records_populates_structured_layers(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)

            applied = MemoryMigrator.from_workspace(workspace).bootstrap_core_records()
            api = AdminAPI.from_workspace(workspace)

            self.assertGreaterEqual(len(applied["preferences"]), 4)
            self.assertGreaterEqual(len(applied["tasks"]), 2)
            self.assertGreaterEqual(len(applied["episodes"]), 3)
            self.assertIsNotNone(api.preferences.get("user.communication_style"))
            self.assertIsNotNone(api.tasks.get("task.claw-memory-layering"))
            self.assertIsNotNone(api.episodes.get("episode.disable-autorecall-2026-03"))
            self.assertIsNotNone(api.facts.get_fact("pansou.mirror_priority"))

    def test_write_bootstrap_report_creates_json_report(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)

            path = MemoryMigrator.from_workspace(workspace).write_bootstrap_report()

            self.assertTrue(path.exists())
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "memory-bootstrap-report.v1")
            self.assertIn("post_governance", report)


if __name__ == "__main__":
    unittest.main()
