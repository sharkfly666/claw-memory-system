from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import importlib
import importlib.util
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.episodes_store import EpisodesStore
from claw_memory_system.facts_store import FactsStore
from claw_memory_system.preferences_store import PreferencesStore
from claw_memory_system.session_store import SessionStore
from claw_memory_system.tasks_store import TasksStore


class StructuredGraphBuilderTest(unittest.TestCase):
    def test_build_structured_graph_projects_records_into_nodes_and_edges(self) -> None:
        spec = importlib.util.find_spec("claw_memory_system.graph_builder")
        self.assertIsNotNone(spec, "claw_memory_system.graph_builder module is missing")

        module = importlib.import_module("claw_memory_system.graph_builder")
        build_graph = getattr(module, "build_structured_graph", None)
        self.assertTrue(callable(build_graph), "build_structured_graph() is missing")

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            facts = FactsStore(base / "facts.json")
            preferences = PreferencesStore(base / "preferences.json")
            tasks = TasksStore(base / "tasks.json")
            episodes = EpisodesStore(base / "episodes.json")
            sessions = SessionStore(base / "session.json")

            facts.upsert_simple(
                "agent.workspace_path",
                "/tmp/demo",
                value_type="string",
                source="test",
                aliases=["workspace"],
                tags=["runtime"],
                notes="Workspace root",
            )
            preferences.upsert(
                "user.communication_style.direct",
                {
                    "value": True,
                    "value_type": "boolean",
                    "notes": "Answer directly",
                    "aliases": ["direct"],
                    "tags": ["style"],
                    "status": "active",
                },
            )
            tasks.upsert(
                "task-beta-graph",
                {
                    "title": "Build graph refresh",
                    "summary": "Connect structured memory to graph view.",
                    "related_entities": ["openclaw", "beta"],
                    "aliases": ["graph-refresh"],
                    "tags": ["beta", "memory"],
                    "state": "active",
                },
            )
            episodes.upsert(
                "ep-beta-graph",
                {
                    "title": "Graph backend gap",
                    "summary": "Confirmed graph store stayed empty.",
                    "task_ids": ["task-beta-graph"],
                    "aliases": ["graph-gap"],
                    "tags": ["beta"],
                    "status": "active",
                },
            )
            sessions.upsert(
                "main",
                {
                    "active_task_ids": ["task-beta-graph"],
                    "active_topics": ["openclaw", "beta"],
                    "status": "active",
                },
            )

            graph = build_graph(
                facts=facts,
                preferences=preferences,
                tasks=tasks,
                episodes=episodes,
                sessions=sessions,
            )

        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])

        self.assertIn("fact:agent.workspace_path", nodes)
        self.assertIn("preference:user.communication_style.direct", nodes)
        self.assertIn("task:task-beta-graph", nodes)
        self.assertIn("episode:ep-beta-graph", nodes)
        self.assertIn("session:main", nodes)
        self.assertIn("entity:openclaw", nodes)
        self.assertIn("tag:beta", nodes)
        self.assertIn("alias:graph-refresh", nodes)

        self.assertIn(
            ("task:task-beta-graph", "related_to", "entity:openclaw"),
            {(edge["source"], edge["relation"], edge["target"]) for edge in edges},
        )
        self.assertIn(
            ("episode:ep-beta-graph", "references_task", "task:task-beta-graph"),
            {(edge["source"], edge["relation"], edge["target"]) for edge in edges},
        )
        self.assertIn(
            ("session:main", "tracks_task", "task:task-beta-graph"),
            {(edge["source"], edge["relation"], edge["target"]) for edge in edges},
        )

    def test_build_structured_graph_deduplicates_repeated_relationships(self) -> None:
        spec = importlib.util.find_spec("claw_memory_system.graph_builder")
        self.assertIsNotNone(spec, "claw_memory_system.graph_builder module is missing")

        module = importlib.import_module("claw_memory_system.graph_builder")
        build_graph = getattr(module, "build_structured_graph", None)
        self.assertTrue(callable(build_graph), "build_structured_graph() is missing")

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            facts = FactsStore(base / "facts.json")
            preferences = PreferencesStore(base / "preferences.json")
            tasks = TasksStore(base / "tasks.json")
            episodes = EpisodesStore(base / "episodes.json")
            sessions = SessionStore(base / "session.json")

            tasks.upsert(
                "task-dup",
                {
                    "title": "Deduplicate graph edges",
                    "related_entities": ["openclaw", "openclaw"],
                    "aliases": ["same", "same"],
                    "tags": ["beta", "beta"],
                },
            )
            episodes.upsert(
                "ep-dup",
                {
                    "title": "Repeated references",
                    "task_ids": ["task-dup", "task-dup"],
                    "tags": ["beta", "beta"],
                },
            )
            sessions.upsert(
                "main",
                {
                    "active_task_ids": ["task-dup", "task-dup"],
                    "active_topics": ["openclaw", "openclaw"],
                },
            )

            graph = build_graph(
                facts=facts,
                preferences=preferences,
                tasks=tasks,
                episodes=episodes,
                sessions=sessions,
            )

        edges = [(edge["source"], edge["relation"], edge["target"]) for edge in graph.get("edges", [])]

        self.assertEqual(edges.count(("task:task-dup", "related_to", "entity:openclaw")), 1)
        self.assertEqual(edges.count(("task:task-dup", "has_alias", "alias:same")), 1)
        self.assertEqual(edges.count(("task:task-dup", "tagged_with", "tag:beta")), 1)
        self.assertEqual(edges.count(("episode:ep-dup", "references_task", "task:task-dup")), 1)
        self.assertEqual(edges.count(("session:main", "tracks_task", "task:task-dup")), 1)


if __name__ == "__main__":
    unittest.main()
