from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.record_equivalence import records_equivalent


class RecordEquivalenceTest(unittest.TestCase):
    def test_equivalent_records_ignore_timestamps_and_list_order(self) -> None:
        a = {
            "summary": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "tags": ["preference", "autocaptured"],
            "aliases": ["a", "b"],
            "updated_at": "1",
        }
        b = {
            "summary": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
            "tags": ["autocaptured", "preference"],
            "aliases": ["b", "a"],
            "updated_at": "2",
        }
        self.assertTrue(records_equivalent(a, b))


if __name__ == "__main__":
    unittest.main()
