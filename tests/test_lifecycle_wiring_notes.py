from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LifecycleWiringNotesTest(unittest.TestCase):
    def test_index_contains_agent_end_queue_only_wiring(self) -> None:
        text = (ROOT / 'index.ts').read_text(encoding='utf-8')
        self.assertIn('api.on("agent_end"', text)
        self.assertIn('claw_memory_queue_turn_candidates', text)
        self.assertIn('--user-text', text)
        self.assertIn('--assistant-text', text)
        self.assertIn('--tool-summary', text)


if __name__ == '__main__':
    unittest.main()
