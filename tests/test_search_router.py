from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system import (
    EpisodesStore,
    FactsStore,
    GraphStore,
    PreferencesStore,
    SessionStore,
    TasksStore,
)
from claw_memory_system.retrieval_inspector import RetrievalInspector
from claw_memory_system.search_router import SearchRouter


class RetrievalInspectorTest(unittest.TestCase):
    def test_inspect_includes_exact_and_vector_hits_when_configured(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            facts = FactsStore(base / "facts.json")
            preferences = PreferencesStore(base / "preferences.json")
            tasks = TasksStore(base / "tasks.json")
            episodes = EpisodesStore(base / "episodes.json")
            sessions = SessionStore(base / "sessions.json")
            graph = GraphStore(base / "graph.json")

            facts.upsert_simple(
                "agent.workspace_path",
                "/tmp/workspace",
                value_type="string",
                source="unit-test",
            )

            router = SearchRouter(
                facts=facts,
                preferences=preferences,
                tasks=tasks,
                episodes=episodes,
                sessions=sessions,
                graph=graph,
                exact_query=lambda query: [{"source": "exact", "id": "fts:1", "record": {"query": query}, "score": 0.9}],
                vector_query=lambda query: [{"source": "vector", "id": "vec:1", "record": {"query": query}, "score": 0.7}],
            )

            result = RetrievalInspector(router).inspect("workspace path")

            self.assertIn("exact", result["layer_hits"])
            self.assertEqual(result["layer_hits"]["exact"], 1)
            self.assertIn("vector", result["layer_hits"])
            self.assertEqual(result["layer_hits"]["vector"], 1)


if __name__ == "__main__":
    unittest.main()
