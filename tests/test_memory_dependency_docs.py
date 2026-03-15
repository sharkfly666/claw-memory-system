from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MemoryDependencyDocsTest(unittest.TestCase):
    def test_readmes_and_quickstart_mention_memory_lancedb_pro(self) -> None:
        files = [
            ROOT / 'README.md',
            ROOT / 'README.zh-CN.md',
            ROOT / 'docs' / 'quickstart-openclaw-chat-install.zh-CN.md',
            ROOT / 'docs' / 'full-enable-guide.zh-CN.md',
        ]
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertIn('memory-lancedb-pro', text, f'{path} should mention memory-lancedb-pro')

    def test_plugin_manifest_notes_mention_tested_stack(self) -> None:
        manifest = json.loads((ROOT / 'openclaw.plugin.json').read_text(encoding='utf-8'))
        notes = '\n'.join(manifest['setup']['notes'])
        self.assertIn('memory-lancedb-pro', notes)
        self.assertIn('1.1.0-beta.8', notes)


if __name__ == '__main__':
    unittest.main()
