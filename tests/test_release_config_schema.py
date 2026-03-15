from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseConfigSchemaTest(unittest.TestCase):
    def test_plugin_config_exposes_release_safe_defaults(self) -> None:
        plugin = json.loads((ROOT / 'openclaw.plugin.json').read_text(encoding='utf-8'))
        props = plugin['configSchema']['properties']
        self.assertFalse(props['autoTurnCapture']['default'])
        self.assertTrue(props['autoTurnQueueOnly']['default'])
        self.assertEqual(props['turnCaptureMinConfidence']['default'], 0.88)
        self.assertTrue(props['batchGovernanceEnabled']['default'])
        self.assertEqual(props['batchGovernanceEvery']['default'], '6h')


if __name__ == '__main__':
    unittest.main()
