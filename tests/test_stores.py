from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.facts_store import FactsStore


class FactsStoreTest(unittest.TestCase):
    def test_upsert_simple_creates_missing_store_and_history(self) -> None:
        with TemporaryDirectory() as tmp:
            facts_path = Path(tmp) / "nested" / "facts.json"
            history_path = Path(tmp) / "nested" / "facts.history.jsonl"
            store = FactsStore(facts_path, history_path)

            first = store.upsert_simple(
                "agent.primary_model",
                "gpt-5",
                value_type="string",
                source="unit-test",
            )
            second = store.upsert_simple(
                "agent.primary_model",
                "gpt-5.1",
                value_type="string",
                source="unit-test",
            )

            self.assertTrue(facts_path.exists())
            self.assertTrue(history_path.exists())
            self.assertEqual(first["created_at"], second["created_at"])
            self.assertEqual(store.get_fact("agent.primary_model")["value"], "gpt-5.1")

            history_lines = history_path.read_text().strip().splitlines()
            self.assertEqual(len(history_lines), 1)
            self.assertEqual(json.loads(history_lines[0])["old"]["value"], "gpt-5")


if __name__ == "__main__":
    unittest.main()
