from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.memory_merge import merge_record


class MemoryMergeTest(unittest.TestCase):
    def test_merge_record_combines_lists_and_prefers_richer_summary(self) -> None:
        existing = {
            "summary": "直接",
            "aliases": ["少废话"],
            "tags": ["communication"],
            "importance": "medium",
        }
        incoming = {
            "summary": "用户偏好直接、高效、少废话的沟通方式。",
            "aliases": ["高效沟通"],
            "tags": ["style"],
            "importance": "high",
        }

        merged = merge_record(existing, incoming, layer="preferences")

        self.assertEqual(merged["summary"], "用户偏好直接、高效、少废话的沟通方式。")
        self.assertIn("少废话", merged["aliases"])
        self.assertIn("高效沟通", merged["aliases"])
        self.assertIn("communication", merged["tags"])
        self.assertIn("style", merged["tags"])
        self.assertEqual(merged["importance"], "high")


if __name__ == "__main__":
    unittest.main()
