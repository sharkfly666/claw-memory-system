from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LifecycleQueueSmokeScriptTest(unittest.TestCase):
    def test_lifecycle_queue_smoke_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'run_lifecycle_queue_smoke.py')],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        self.assertGreaterEqual(payload['queued_count'], 1)


if __name__ == '__main__':
    unittest.main()
