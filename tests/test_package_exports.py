from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class PackageExportsTest(unittest.TestCase):
    def test_skill_proposals_store_is_exported_from_package_root(self) -> None:
        from claw_memory_system import SkillProposalsStore

        self.assertEqual(SkillProposalsStore.__name__, "SkillProposalsStore")


if __name__ == "__main__":
    unittest.main()
