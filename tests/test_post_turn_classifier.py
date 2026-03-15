from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.post_turn_classifier import classify_turn


class PostTurnClassifierTest(unittest.TestCase):
    def test_classify_preference_turn(self) -> None:
        result = classify_turn(
            Path('/tmp'),
            user_text='以后涉及 GitHub 下载优先用 gh，不要 git clone',
        )
        self.assertTrue(result['should_store'])
        layers = {item['layer'] for item in result['candidates']}
        self.assertIn('preferences', layers)
        self.assertEqual(result['mode'], 'direct')

    def test_classify_task_turn(self) -> None:
        result = classify_turn(
            Path('/tmp'),
            user_text='继续优化 daily-briefing，下一步修 timeout 和投递',
        )
        self.assertTrue(result['should_store'])
        layers = {item['layer'] for item in result['candidates']}
        self.assertIn('tasks', layers)


if __name__ == '__main__':
    unittest.main()
