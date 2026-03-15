from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadmeLanguageSwitchAndQuickstartTest(unittest.TestCase):
    def test_readmes_have_language_switch_links(self) -> None:
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        zh = (ROOT / 'README.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('README.zh-CN.md', readme)
        self.assertIn('README.md', zh)

    def test_root_readmes_expose_quickstart_install_commands(self) -> None:
        for path in [ROOT / 'README.md', ROOT / 'README.zh-CN.md']:
            text = path.read_text(encoding='utf-8')
            self.assertIn('openclaw plugins install memory-lancedb-pro', text)
            self.assertIn('openclaw plugins enable claw-memory-system', text)
            self.assertIn('claw_memory_bootstrap', text)


if __name__ == '__main__':
    unittest.main()
