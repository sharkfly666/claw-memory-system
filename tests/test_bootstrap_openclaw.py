from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.bootstrap_openclaw_instance import bootstrap


class BootstrapWorkspaceWrappersTest(unittest.TestCase):
    def test_bootstrap_generates_runnable_facts_cli_wrapper(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)

            wrapper = workspace / "memory-system" / "facts" / "facts_cli.py"
            result = subprocess.run(
                [sys.executable, str(wrapper), "list"],
                cwd=workspace,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "{}")

    def test_bootstrap_generates_runnable_build_pageindex_wrapper(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text("# Primary model\nUses GPT-5.\n")

            wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
            result = subprocess.run(
                [sys.executable, str(wrapper)],
                cwd=workspace,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((workspace / "memory-system" / "index" / "pageindex.sqlite").exists())
            self.assertIn("Indexed", result.stdout)

    def test_bootstrap_generates_runnable_search_pageindex_wrapper(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text("# Primary model\nUses GPT-5.\n")

            build_wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
            build_result = subprocess.run(
                [sys.executable, str(build_wrapper)],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)

            search_wrapper = workspace / "memory-system" / "index" / "search_pageindex.py"
            result = subprocess.run(
                [sys.executable, str(search_wrapper), "primary"],
                cwd=workspace,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("memory_md", result.stdout)


if __name__ == "__main__":
    unittest.main()
