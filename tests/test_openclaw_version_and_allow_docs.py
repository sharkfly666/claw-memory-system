from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OpenClawVersionAndAllowDocsTest(unittest.TestCase):
    def test_docs_mention_openclaw_2026_3_12_plus(self) -> None:
        files = [
            ROOT / 'README.md',
            ROOT / 'README.zh-CN.md',
            ROOT / 'docs' / 'companion-dependencies.zh-CN.md',
        ]
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertIn('2026.3.12', text)

    def test_docs_mention_plugins_allow_guidance(self) -> None:
        files = [
            ROOT / 'README.md',
            ROOT / 'README.zh-CN.md',
            ROOT / 'docs' / 'quickstart-openclaw-chat-install.zh-CN.md',
        ]
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertIn('plugins.allow', text)


if __name__ == '__main__':
    unittest.main()
