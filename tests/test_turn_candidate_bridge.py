from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.turn_candidate_bridge import TurnCandidateBridge


class TurnCandidateBridgeTest(unittest.TestCase):
    def test_classify_and_queue_portable_candidates(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            bridge = TurnCandidateBridge.from_workspace(workspace)
            result = bridge.classify_and_queue(
                user_text="以后涉及 GitHub 下载优先用 gh，不要 git clone"
            )
            second = bridge.classify_and_queue(
                user_text="以后涉及 GitHub 下载优先用 gh，不要 git clone"
            )
            self.assertEqual(result["schema_version"], "turn-candidate-bridge.v1")
            self.assertEqual(result["queued_count"], 1)
            self.assertEqual(second["queued_count"], 0)
            queued = result["queued"][0]
            self.assertEqual(queued["target_layer"], "preferences")
            store = json.loads((workspace / "memory-system" / "stores" / "v2" / "turn_candidates.json").read_text(encoding="utf-8"))
            self.assertEqual(len(store["candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
