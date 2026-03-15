from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallEnableDocsTest(unittest.TestCase):
    def test_quickstart_doc_mentions_plugin_install_enable_and_bootstrap(self) -> None:
        text = (ROOT / 'docs' / 'quickstart-openclaw-chat-install.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('openclaw plugins install', text)
        self.assertIn('openclaw plugins enable claw-memory-system', text)
        self.assertIn('claw_memory_bootstrap', text)
        self.assertIn('claw_memory_batch_governance', text)

    def test_full_enable_doc_mentions_auto_turn_capture_and_queue_only(self) -> None:
        text = (ROOT / 'docs' / 'full-enable-guide.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('autoTurnCapture', text)
        self.assertIn('autoTurnQueueOnly', text)
        self.assertIn('queue-only', text)


if __name__ == '__main__':
    unittest.main()
