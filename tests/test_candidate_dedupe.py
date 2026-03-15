from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.candidate_dedupe import dedupe_key_for_candidate


class CandidateDedupeTest(unittest.TestCase):
    def test_same_candidate_has_same_dedupe_key(self) -> None:
        a = {
            "target_layer": "preferences",
            "summary": "偏好候选：以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "user_text": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "reason": "contains stable preference markers",
        }
        b = dict(a)
        self.assertEqual(dedupe_key_for_candidate(a), dedupe_key_for_candidate(b))


if __name__ == "__main__":
    unittest.main()
