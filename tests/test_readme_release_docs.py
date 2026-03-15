from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadmeReleaseDocsTest(unittest.TestCase):
    def test_root_readme_mentions_safe_defaults(self) -> None:
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('autoTurnCapture = false', text)
        self.assertIn('queue first, govern second, absorb third', text)

    def test_release_notes_document_known_limitations(self) -> None:
        text = (ROOT / 'docs' / 'release-notes-v0.1.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('已知限制', text)
        self.assertIn('规则型', text)
        self.assertIn('queue-only', text)


if __name__ == '__main__':
    unittest.main()
