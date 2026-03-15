from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_api import AdminAPI
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.model_profiles_store import ModelProfilesStore


def write_semantic_provider_script(path: Path) -> None:
    path.write_text(
        """import json
import sys

mode = sys.argv[1]

if mode == "search":
    query = sys.argv[2]
    limit = int(sys.argv[3])
    provider = sys.argv[4]
    print(json.dumps([
        {
            "entry": {
                "id": f"{provider}-1",
                "scope": "global",
                "category": "conversation",
                "text": f"{provider} hit for {query}",
                "timestamp": "2026-03-13T00:00:00Z",
                "metadata": {
                    "limit": limit,
                    "provider": provider,
                },
            },
            "score": 0.88,
            "sources": {
                "semantic": 0.81,
            },
        }
    ]))
elif mode == "stats":
    print(json.dumps({
        "memory": {
            "totalCount": 9,
            "scopeCounts": {
                "agent:main": 9,
            },
            "categoryCounts": {
                "other": 6,
                "fact": 3,
            },
        },
        "retrieval": {
            "mode": "hybrid",
            "hasFtsSupport": True,
        },
    }))
elif mode == "list":
    limit = int(sys.argv[2])
    provider = sys.argv[3]
    print(json.dumps([
        {
            "id": f"{provider}:recent:1",
            "text": "Semantic dashboard recent memory",
            "scope": "agent:main",
            "category": "other",
            "importance": 0.91,
            "timestamp": 1773394513647,
            "metadata": json.dumps({
                "source": {
                    "plugin": provider,
                }
            }),
        }
    ][:limit]))
else:
    raise SystemExit(f"unsupported mode: {mode}")
""",
        encoding="utf-8",
    )


class AdminAPITest(unittest.TestCase):
    def test_from_workspace_connects_exact_search_when_pageindex_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text("# Primary model\nUse GPT-5 for the default assistant.\n")

            build_wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
            build_result = subprocess.run(
                [sys.executable, str(build_wrapper)],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)

            api = AdminAPI.from_workspace(workspace)
            result = api.inspect_query("primary model")

            self.assertGreaterEqual(result["layer_hits"].get("exact", 0), 1)
            self.assertTrue(any(hit.get("source") == "exact" for hit in result["final_hits"]))

    def test_from_workspace_picks_up_pageindex_built_after_api_creation(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text("# Primary model\nUse GPT-5 for the default assistant.\n")

            api = AdminAPI.from_workspace(workspace)

            build_wrapper = workspace / "memory-system" / "index" / "build_pageindex.py"
            build_result = subprocess.run(
                [sys.executable, str(build_wrapper)],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)

            result = api.inspect_query("primary model")

            self.assertGreaterEqual(result["layer_hits"].get("exact", 0), 1)

    def test_from_workspace_connects_semantic_provider_from_models_store(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            script_path = Path(tmp) / "semantic_provider.py"
            write_semantic_provider_script(script_path)
            models.upsert(
                "memory",
                "default",
                {
                    "provider": "memory-lancedb-pro",
                    "enabled": True,
                    "active": True,
                    "command": [sys.executable, str(script_path), "search", "{query}", "{limit}", "memory-lancedb-pro"],
                    "stats_command": [sys.executable, str(script_path), "stats"],
                    "list_command": [sys.executable, str(script_path), "list", "{limit}", "memory-lancedb-pro"],
                },
            )

            api = AdminAPI.from_workspace(workspace)
            result = api.inspect_query("semantic memory history")

            self.assertGreaterEqual(result["layer_hits"].get("vector", 0), 1)
            vector_hits = [hit for hit in result["final_hits"] if hit.get("source") == "vector"]
            self.assertTrue(vector_hits)
            self.assertEqual(vector_hits[0]["record"]["provider"], "memory-lancedb-pro")
            self.assertEqual(vector_hits[0]["record"]["metadata"]["limit"], 10)

            overview = api.semantic_overview(limit=1)
            self.assertTrue(overview["configured"])
            self.assertEqual(overview["provider"], "memory-lancedb-pro")
            self.assertEqual(overview["total_count"], 9)
            self.assertEqual(overview["scope_counts"]["agent:main"], 9)
            self.assertEqual(overview["category_counts"]["fact"], 3)
            self.assertEqual(overview["retrieval"]["mode"], "hybrid")
            self.assertEqual(overview["recent"][0]["text"], "Semantic dashboard recent memory")

    def test_refresh_graph_response_rebuilds_graph_from_structured_memory(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            api.facts.upsert_simple(
                "agent.workspace_path",
                "/tmp/demo",
                value_type="string",
                source="test",
                tags=["runtime"],
            )
            api.tasks.upsert(
                "task-beta-graph",
                {
                    "title": "Build graph refresh",
                    "summary": "Connect structured memory to graph view.",
                    "related_entities": ["openclaw"],
                    "tags": ["beta"],
                },
            )
            api.episodes.upsert(
                "ep-beta-graph",
                {
                    "title": "Graph backend gap",
                    "summary": "Confirmed graph store stayed empty.",
                    "task_ids": ["task-beta-graph"],
                },
            )
            api.sessions.upsert(
                "main",
                {
                    "active_task_ids": ["task-beta-graph"],
                    "active_topics": ["openclaw"],
                },
            )

            self.assertTrue(hasattr(api, "refresh_graph_response"), "AdminAPI.refresh_graph_response is missing")
            payload = api.refresh_graph_response()

            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["data"]["graph_nodes"], 4)
            self.assertGreaterEqual(payload["data"]["graph_edges"], 3)
            self.assertIn("task:task-beta-graph", api.graph.list_nodes())
            self.assertTrue(
                any(edge["relation"] == "references_task" for edge in api.graph.list_edges()),
                "expected at least one episode-to-task edge",
            )

    def test_create_migration_candidate_response_rejects_empty_candidate_id(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            payload = api.create_migration_candidate_response(
                "",
                source_layer="episodes",
                source_id="ep-memory-validation",
                target_layer="tasks",
                summary="promote to task",
            )

            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "create_migration_candidate_failed")

    def test_create_migration_candidate_response_rejects_missing_source_layer(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            payload = api.create_migration_candidate_response(
                "cand-1",
                source_layer="",
                source_id="ep-memory-validation",
                target_layer="tasks",
                summary="promote to task",
            )

            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "create_migration_candidate_failed")

    def test_upsert_skill_response_rejects_empty_skill_id(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            payload = api.upsert_skill_response("", {"title": "x"})

            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "upsert_skill_failed")

    def test_upsert_model_profile_response_rejects_empty_name(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            payload = api.upsert_model_profile_response("embedding", "", {"provider": "openai-compatible"})

            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "upsert_model_profile_failed")

    def test_upsert_record_rejects_empty_id_for_generic_task_path(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            with self.assertRaises(ValueError):
                api.upsert_record("tasks", "", {"title": "task"})

    def test_upsert_record_rejects_empty_id_for_skill_proposals(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            api = AdminAPI.from_workspace(workspace)

            with self.assertRaises(ValueError):
                api.upsert_record("skill_proposals", "", {"title": "proposal"})


if __name__ == "__main__":
    unittest.main()
