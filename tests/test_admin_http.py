from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import socketserver
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.admin_http import AdminHttpApp, ThreadedWSGIServer
from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.model_profiles_store import ModelProfilesStore


def write_semantic_provider_script(path: Path) -> None:
    path.write_text(
        """import json
import sys

mode = sys.argv[1]

if mode == "stats":
    print(json.dumps({
        "memory": {
            "totalCount": 11,
            "scopeCounts": {
                "agent:main": 10,
                "global": 1,
            },
            "categoryCounts": {
                "other": 8,
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
    print(json.dumps([
        {
            "id": "memory-lancedb-pro:recent:1",
            "text": "Semantic console preview row",
            "scope": "agent:main",
            "category": "other",
            "importance": 0.88,
            "timestamp": 1773394513647,
            "metadata": json.dumps({
                "source": {
                    "plugin": "memory-lancedb-pro",
                }
            }),
        }
    ][:limit]))
elif mode == "search":
    query = sys.argv[2]
    limit = int(sys.argv[3])
    print(json.dumps([
        {
            "entry": {
                "id": "memory-lancedb-pro-hit-1",
                "scope": "agent:main",
                "category": "other",
                "text": f"memory-lancedb-pro hit for {query}",
                "timestamp": "2026-03-13T00:00:00Z",
                "metadata": {"limit": limit},
            },
            "score": 0.8,
            "sources": {"semantic": 0.8},
        }
    ]))
else:
    raise SystemExit(f"unsupported mode: {mode}")
""",
        encoding="utf-8",
    )


def call_app(app: AdminHttpApp, *, method: str, path: str, query: str = "", body: bytes = b"{}", headers: dict[str, str] | None = None) -> tuple[str, dict]:
    captured: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = headers

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    if headers:
        for key, value in headers.items():
            environ[key] = value
    response = b"".join(app(environ, start_response))
    return captured["status"], json.loads(response.decode("utf-8"))


def call_app_with_headers(
    app: AdminHttpApp,
    *,
    method: str,
    path: str,
    query: str = "",
    body: bytes = b"{}",
    headers: dict[str, str] | None = None,
) -> tuple[str, dict, dict[str, str]]:
    captured: dict[str, object] = {}

    def start_response(status: str, response_headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = {key: value for key, value in response_headers}

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    if headers:
        for key, value in headers.items():
            environ[key] = value
    response = b"".join(app(environ, start_response))
    return captured["status"], json.loads(response.decode("utf-8")), captured["headers"]


class AdminHttpAppTest(unittest.TestCase):
    def test_threaded_wsgi_server_supports_parallel_requests(self) -> None:
        self.assertTrue(issubclass(ThreadedWSGIServer, socketserver.ThreadingMixIn))
        self.assertTrue(ThreadedWSGIServer.daemon_threads)

    def test_semantic_overview_returns_semantic_memory_totals_and_recent_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            script_path = Path(tmp) / "semantic_provider.py"
            write_semantic_provider_script(script_path)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            models.upsert(
                "memory",
                "default",
                {
                    "provider": "memory-lancedb-pro",
                    "enabled": True,
                    "active": True,
                    "command": [sys.executable, str(script_path), "search", "{query}", "{limit}"],
                    "stats_command": [sys.executable, str(script_path), "stats"],
                    "list_command": [sys.executable, str(script_path), "list", "{limit}"],
                },
            )
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="GET",
                path="/api/semantic-overview",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["data"]["configured"])
            self.assertEqual(payload["data"]["total_count"], 11)
            self.assertEqual(payload["data"]["scope_counts"]["agent:main"], 10)
            self.assertEqual(payload["data"]["recent"][0]["text"], "Semantic console preview row")
            self.assertEqual(payload["meta"]["provider"], "memory-lancedb-pro")

    def test_governance_report_endpoint_returns_structured_report(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="GET",
                path="/api/governance-report",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["data"]["schema_version"], "memory-governance-report.v1")

    def test_memory_bootstrap_endpoint_populates_core_records(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/memory-bootstrap",
                body=b"{}",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertIn("user.communication_style", payload["data"]["preferences"])

    def test_candidate_drafts_endpoint_returns_drafts(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text(
                "用户偏好：直接高效，少废话。\n待办：继续优化 daily-briefing。\n",
                encoding="utf-8",
            )
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="GET",
                path="/api/candidate-drafts",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["data"]["count"], 2)

    def test_candidate_draft_preview_endpoint_returns_conflicts(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)
            call_app(
                app,
                method="POST",
                path="/api/preference",
                body=json.dumps({
                    "key": "user.communication_style",
                    "value": "直接",
                    "value_type": "string",
                    "aliases": ["少废话"],
                    "tags": ["communication"],
                    "status": "active",
                }).encode("utf-8"),
            )

            status, payload = call_app(
                app,
                method="POST",
                path="/api/candidate-draft/preview",
                body=json.dumps({
                    "target_layer": "preferences",
                    "target_id": "user.communication_style",
                    "record": {"summary": "更新版", "aliases": ["高效"], "tags": ["communication"], "status": "active"},
                }).encode("utf-8"),
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(len(payload["data"]["conflicts"]), 1)

    def test_batch_governance_endpoint_runs_and_returns_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            (workspace / "MEMORY.md").write_text(
                "用户偏好：直接高效，少废话。\n待办：继续优化 daily-briefing。\n问题：之前因 timeout 做过修复。\n",
                encoding="utf-8",
            )
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/batch-governance",
                body=json.dumps({"auto_apply_safe": True, "refresh_graph": True}).encode("utf-8"),
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["data"]["summary"]["applied_count"], 1)

    def test_options_preflight_allows_json_post_to_preference_endpoint(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload, headers = call_app_with_headers(
                app,
                method="OPTIONS",
                path="/api/preference",
                body=b"",
                headers={
                    "HTTP_ORIGIN": "http://127.0.0.1:18080",
                    "HTTP_ACCESS_CONTROL_REQUEST_METHOD": "POST",
                    "HTTP_ACCESS_CONTROL_REQUEST_HEADERS": "content-type",
                },
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
            self.assertIn("POST", headers["Access-Control-Allow-Methods"])
            self.assertIn("OPTIONS", headers["Access-Control-Allow-Methods"])
            self.assertIn("content-type", headers["Access-Control-Allow-Headers"].lower())

    def test_post_preference_can_be_fetched_via_record_endpoint(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/preference",
                body=json.dumps(
                    {
                        "key": "user.score.threshold",
                        "value": 42.5,
                        "value_type": "number",
                        "notes": "numeric threshold",
                        "strength": 0.75,
                        "aliases": ["alpha", "beta"],
                        "tags": ["memory", "beta"],
                    }
                ).encode("utf-8"),
            )
            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/record",
                query="layer=preferences&id=user.score.threshold",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["data"]["value"], 42.5)
            self.assertEqual(payload["data"]["value_type"], "number")
            self.assertEqual(payload["meta"]["layer"], "preferences")

    def test_post_task_can_be_listed_and_fetched(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/task",
                body=json.dumps(
                    {
                        "task_id": "task-console-beta",
                        "title": "Stabilize memory console beta",
                        "summary": "Close backend and UI gaps.",
                        "next_action": "Finish write-flow validation.",
                        "priority": "high",
                        "state": "active",
                        "importance": "high",
                        "related_entities": ["memory-console", "beta"],
                    }
                ).encode("utf-8"),
            )
            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/layer",
                query="layer=tasks",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["meta"]["count"], 1)
            self.assertIn("task-console-beta", payload["data"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/record",
                query="layer=tasks&id=task-console-beta",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["data"]["next_action"], "Finish write-flow validation.")
            self.assertEqual(payload["data"]["related_entities"], ["memory-console", "beta"])

    def test_post_episode_can_be_listed_and_fetched(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/episode",
                body=json.dumps(
                    {
                        "episode_id": "ep-console-beta-progress",
                        "title": "Memory console beta stabilization",
                        "summary": "Stabilized wrappers and write paths.",
                        "status": "active",
                        "task_ids": ["task-console-beta"],
                        "importance": "high",
                    }
                ).encode("utf-8"),
            )
            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/layer",
                query="layer=episodes",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["meta"]["count"], 1)
            self.assertIn("ep-console-beta-progress", payload["data"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/record",
                query="layer=episodes&id=ep-console-beta-progress",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["data"]["task_ids"], ["task-console-beta"])
            self.assertEqual(payload["data"]["importance"], "high")

    def test_post_graph_refresh_rebuilds_graph_layer(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            app.api.facts.upsert_simple(
                "agent.workspace_path",
                "/tmp/demo",
                value_type="string",
                source="test",
                tags=["runtime"],
            )
            app.api.tasks.upsert(
                "task-beta-graph",
                {
                    "title": "Build graph refresh",
                    "summary": "Connect structured memory to graph view.",
                    "related_entities": ["openclaw"],
                    "tags": ["beta"],
                },
            )
            app.api.episodes.upsert(
                "ep-beta-graph",
                {
                    "title": "Graph backend gap",
                    "summary": "Confirmed graph store stayed empty.",
                    "task_ids": ["task-beta-graph"],
                },
            )

            status, payload = call_app(
                app,
                method="POST",
                path="/api/graph/refresh",
                body=b"{}",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["data"]["graph_nodes"], 4)
            self.assertGreaterEqual(payload["data"]["graph_edges"], 2)

            status, payload = call_app(
                app,
                method="GET",
                path="/api/layer",
                query="layer=graph.nodes",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertIn("task:task-beta-graph", payload["data"])

    def test_post_model_profile_can_be_fetched_via_record_endpoint(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/model-profile",
                body=json.dumps(
                    {
                        "category": "embedding",
                        "name": "default-embed",
                        "provider": "openai-compatible",
                        "model": "text-embedding-3-large",
                    }
                ).encode("utf-8"),
            )
            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/record",
                query="layer=models&id=embedding/default-embed",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["data"]["name"], "default-embed")
            self.assertEqual(payload["meta"]["layer"], "models")

    def test_models_layer_count_reflects_total_profiles_not_category_buckets(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            for category, name in [("embedding", "default-embed"), ("summarization", "default-sum")]:
                status, payload = call_app(
                    app,
                    method="POST",
                    path="/api/model-profile",
                    body=json.dumps(
                        {
                            "category": category,
                            "name": name,
                            "provider": "openai-compatible",
                            "model": "demo-model",
                        }
                    ).encode("utf-8"),
                )
                self.assertTrue(status.startswith("200"), status)
                self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/layer",
                query="layer=models",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["meta"]["count"], 2)

    def test_summary_counts_model_profiles_from_custom_categories(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/model-profile",
                body=json.dumps(
                    {
                        "category": "reranking",
                        "name": "default-reranker",
                        "provider": "openai-compatible",
                        "model": "rerank-demo",
                    }
                ).encode("utf-8"),
            )
            self.assertTrue(status.startswith("200"), status)
            self.assertTrue(payload["ok"])

            status, payload = call_app(
                app,
                method="GET",
                path="/api/summary",
                body=b"",
            )

            self.assertTrue(status.startswith("200"), status)
            self.assertEqual(payload["data"]["model_profiles"], 1)

    def test_get_missing_report_returns_not_found(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="GET",
                path="/api/report",
                query="name=missing-report",
                body=b"",
            )

            self.assertTrue(status.startswith("404"), status)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "report_not_found")

    def test_post_invalid_json_returns_bad_request(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(app, method="POST", path="/api/skill", body=b"{")

            self.assertTrue(status.startswith("400"), status)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "invalid_json")

    def test_post_migration_candidate_requires_candidate_id(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            app = AdminHttpApp(workspace)

            status, payload = call_app(
                app,
                method="POST",
                path="/api/migration-candidate",
                body=json.dumps(
                    {
                        "source_layer": "episodes",
                        "source_id": "ep-memory-validation",
                        "target_layer": "tasks",
                        "summary": "promote to task",
                    }
                ).encode("utf-8"),
            )

            self.assertTrue(status.startswith("400"), status)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
