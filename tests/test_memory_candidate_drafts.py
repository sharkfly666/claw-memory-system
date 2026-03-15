from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_api import AdminAPI
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.memory_candidate_drafts import MemoryCandidateDrafts


class MemoryCandidateDraftsTest(unittest.TestCase):
    def test_generate_candidate_drafts_from_markdown_candidates(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text(
                "用户偏好：直接高效，少废话。\n待办：继续优化 daily-briefing。\n问题：之前因 timeout 做过修复。\n",
                encoding="utf-8",
            )
            drafts = MemoryCandidateDrafts.from_workspace(workspace).generate()

            self.assertGreaterEqual(drafts["count"], 3)
            layers = {item["target_layer"] for item in drafts["drafts"]}
            self.assertIn("preferences", layers)
            self.assertIn("tasks", layers)
            self.assertIn("episodes", layers)

    def test_apply_candidate_draft_writes_to_target_layer(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)
            draft = {
                "target_layer": "preferences",
                "target_id": "user.test.preference",
                "record": {
                    "summary": "测试偏好",
                    "aliases": ["测试"],
                    "tags": ["test"],
                    "status": "active",
                },
            }

            payload = api.apply_candidate_draft_response(draft)

            self.assertTrue(payload["ok"])
            self.assertIsNotNone(api.preferences.get("user.test.preference"))

    def test_apply_candidate_draft_merges_existing_record(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)
            api.preferences.upsert(
                "user.test.preference",
                {"summary": "短", "aliases": ["旧"], "tags": ["a"], "status": "active", "importance": "medium"},
            )
            draft = {
                "target_layer": "preferences",
                "target_id": "user.test.preference",
                "record": {
                    "summary": "这是一个更完整的测试偏好描述",
                    "aliases": ["新"],
                    "tags": ["b"],
                    "status": "active",
                    "importance": "high",
                },
            }

            payload = api.apply_candidate_draft_response(draft)

            self.assertTrue(payload["ok"])
            saved = api.preferences.get("user.test.preference")
            self.assertEqual(saved["summary"], "这是一个更完整的测试偏好描述")
            self.assertIn("旧", saved["aliases"])
            self.assertIn("新", saved["aliases"])
            self.assertIn("a", saved["tags"])
            self.assertIn("b", saved["tags"])
            self.assertEqual(saved["importance"], "high")


if __name__ == "__main__":
    unittest.main()
