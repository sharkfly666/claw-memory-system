from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.turn_summary_synth import synthesize_summary


class TurnSummarySynthTest(unittest.TestCase):
    def test_preference_summary_prefers_user_text(self) -> None:
        summary = synthesize_summary(
            'preferences',
            user_text='以后涉及 GitHub 下载优先用 gh',
            assistant_text='记住了，后续优先 gh。',
            tool_summary='updated preference candidate',
        )
        self.assertEqual(summary, '以后涉及 GitHub 下载优先用 gh')

    def test_episode_summary_can_include_multiple_parts(self) -> None:
        summary = synthesize_summary(
            'episodes',
            user_text='因为噪声太大，关闭 autoRecall',
            assistant_text='后续改为手动 recall。',
            tool_summary='updated memory config',
        )
        self.assertIn('关闭 autoRecall', summary)
        self.assertIn('手动 recall', summary)


if __name__ == '__main__':
    unittest.main()
