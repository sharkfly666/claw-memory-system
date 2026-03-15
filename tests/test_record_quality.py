from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.record_quality import better_summary, normalize_record, score_summary


class RecordQualityTest(unittest.TestCase):
    def test_better_summary_prefers_human_summary_over_candidate_marker(self) -> None:
        old = "待确认：从 fact:user.communication_style 提炼出的长期偏好候选。"
        new = "用户偏好直接、高效、少废话，回答尽量短。"
        self.assertEqual(better_summary(old, new), new)

    def test_normalize_record_removes_candidate_tag_after_real_summary(self) -> None:
        record = {
            "summary": "用户偏好直接、高效、少废话，回答尽量短。",
            "tags": ["candidate", "communication", "style"],
        }
        normalized = normalize_record(record, layer="preferences")
        self.assertNotIn("candidate", normalized["tags"])
        self.assertIn("preference", normalized["tags"])

    def test_score_summary_penalizes_candidate_marker(self) -> None:
        candidate = score_summary("待确认：从 fact:user.communication_style 提炼出的长期偏好候选。")
        human = score_summary("用户偏好直接、高效、少废话，回答尽量短。")
        self.assertGreater(human, candidate)


if __name__ == "__main__":
    unittest.main()
