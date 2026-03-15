from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WebappSmokeScriptTest(unittest.TestCase):
    def test_run_webapp_smoke_script_exposes_expected_cli_options(self) -> None:
        script = ROOT / "scripts" / "run_webapp_smoke.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--workspace", result.stdout)
        self.assertIn("--api-port", result.stdout)
        self.assertIn("--frontend-port", result.stdout)
        self.assertIn("--output-dir", result.stdout)
        self.assertIn("--browser-executable", result.stdout)


if __name__ == "__main__":
    unittest.main()
