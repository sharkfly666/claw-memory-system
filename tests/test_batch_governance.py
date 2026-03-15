from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.batch_governance import BatchGovernance
from claw_memory_system.bootstrap_openclaw_instance import bootstrap


class BatchGovernanceTest(unittest.TestCase):
    def test_run_batch_governance_auto_applies_safe_drafts(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text(
                "用户偏好：直接高效，少废话。\n待办：继续优化 daily-briefing。\n问题：之前因 timeout 做过修复。\n",
                encoding="utf-8",
            )

            result = BatchGovernance.from_workspace(workspace).run(auto_apply_safe=True, refresh_graph=True)

            self.assertEqual(result["schema_version"], "memory-batch-governance.v1")
            self.assertGreaterEqual(result["summary"]["total_drafts"], 3)
            self.assertGreaterEqual(result["summary"]["applied_count"], 3)
            self.assertIsNotNone(result["graph_summary"])

    def test_write_report_creates_json_file(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text("用户偏好：直接高效，少废话。", encoding="utf-8")

            path = BatchGovernance.from_workspace(workspace).write_report(auto_apply_safe=True, refresh_graph=False)

            self.assertTrue(path.exists())
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "memory-batch-governance.v1")

    def test_batch_governance_consumes_turn_candidates_queue(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            queue_path = workspace / "memory-system" / "stores" / "v2" / "turn_candidates.json"
            queue_path.write_text(json.dumps({
                "schema_version": "turn-candidates.v1",
                "candidates": [{
                    "target_layer": "preferences",
                    "summary": "偏好候选：以后涉及 GitHub 下载优先用 gh，不要 git clone",
                    "confidence": 0.9,
                    "reason": "contains stable preference markers",
                    "source": "post-turn-classifier",
                    "status": "pending",
                    "user_text": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
                    "suggested_id": "pref.github-download",
                }]
            }, ensure_ascii=False), encoding="utf-8")

            result = BatchGovernance.from_workspace(workspace).run(auto_apply_safe=True, refresh_graph=False)

            self.assertGreaterEqual(result["summary"]["queued_drafts"], 1)
            self.assertGreaterEqual(result["summary"]["consumed_pending"], 1)
            self.assertGreaterEqual(result["summary"]["noop_count"], 0)
            saved_queue = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_queue["candidates"][0]["status"], "consumed")


if __name__ == "__main__":
    unittest.main()
