from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.candidate_conversion import queued_candidate_to_draft


class CandidateConversionTest(unittest.TestCase):
    def test_queued_candidate_to_preference_draft(self) -> None:
        draft = queued_candidate_to_draft({
            "target_layer": "preferences",
            "summary": "偏好候选：以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "confidence": 0.9,
            "reason": "contains stable preference markers",
            "user_text": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "suggested_id": "pref.github-download",
        })
        self.assertEqual(draft["target_layer"], "preferences")
        self.assertEqual(draft["target_id"], "pref.github-download")
        self.assertEqual(draft["record"]["summary"], "以后涉及 GitHub 下载优先用 gh，不要 git clone")
        self.assertIn("autocaptured", draft["record"]["tags"])


if __name__ == "__main__":
    unittest.main()
