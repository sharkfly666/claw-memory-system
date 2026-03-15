from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_api import AdminAPI
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.memory_governance_actions import MemoryGovernanceActions


class MemoryGovernanceActionsTest(unittest.TestCase):
    def test_preview_candidate_draft_reports_same_id_conflict(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)
            api.preferences.upsert(
                "user.communication_style",
                {"summary": "直接", "aliases": ["少废话"], "tags": ["communication"], "status": "active"},
            )
            draft = {
                "target_layer": "preferences",
                "target_id": "user.communication_style",
                "record": {"summary": "更新版", "aliases": ["高效"], "tags": ["communication"], "status": "active"},
            }

            preview = MemoryGovernanceActions.from_workspace(workspace).preview_draft_application(draft)

            self.assertTrue(preview["conflicts"])
            conflict_types = [item["type"] for item in preview["conflicts"]]
            self.assertIn("same_id_exists", conflict_types)

    def test_apply_supersede_marks_existing_record(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)
            api.preferences.upsert(
                "user.communication_style_old",
                {"summary": "旧版", "aliases": ["旧"], "tags": ["communication"], "status": "active"},
            )

            payload = api.apply_supersede_response(
                layer="preferences",
                record_id="user.communication_style_old",
                superseded_by="user.communication_style",
            )

            self.assertTrue(payload["ok"])
            updated = api.preferences.get("user.communication_style_old")
            self.assertEqual(updated["status"], "superseded")
            self.assertEqual(updated["superseded_by"], "user.communication_style")


if __name__ == "__main__":
    unittest.main()
