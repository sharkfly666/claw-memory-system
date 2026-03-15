from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.turn_message_extract import extract_turn_texts


class TurnMessageExtractTest(unittest.TestCase):
    def test_extract_turn_texts_from_message_list(self) -> None:
        messages = [
            {"role": "user", "content": "以后涉及 GitHub 下载优先用 gh"},
            {"role": "assistant", "content": "记住了，后续优先 gh。"},
            {"role": "tool", "content": "updated preference candidate"},
        ]
        result = extract_turn_texts(messages)
        self.assertIn("GitHub", result["user_text"])
        self.assertIn("记住了", result["assistant_text"])
        self.assertIn("updated", result["tool_summary"])


if __name__ == "__main__":
    unittest.main()
