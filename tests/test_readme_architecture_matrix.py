from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadmeArchitectureMatrixTest(unittest.TestCase):
    def test_readmes_include_mermaid_architecture_and_capability_table(self) -> None:
        for path in [ROOT / 'README.md', ROOT / 'README.zh-CN.md']:
            text = path.read_text(encoding='utf-8')
            self.assertIn('```mermaid', text)
            self.assertIn('turn_candidates.json', text)
            self.assertIn('| Capability |', text) if path.name == 'README.md' else self.assertIn('| 功能 |', text)
            self.assertIn('memory-lancedb-pro', text)


if __name__ == '__main__':
    unittest.main()
