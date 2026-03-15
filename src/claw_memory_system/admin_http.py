from __future__ import annotations

from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIServer, make_server
import json

from .admin_api import AdminAPI
from .api_response import err
from .report_api import latest_report_response


class InvalidRequestError(ValueError):
    pass


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class AdminHttpApp:
    def __init__(self, workspace_root: Path):
        self.api = AdminAPI.from_workspace(workspace_root)

    def _cors_headers(self, environ) -> list[tuple[str, str]]:
        requested_headers = environ.get("HTTP_ACCESS_CONTROL_REQUEST_HEADERS", "").strip()
        allow_headers = requested_headers or "Content-Type"
        return [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", allow_headers),
            ("Access-Control-Max-Age", "600"),
        ]

    def _read_json_body(self, environ) -> dict:
        size = int(environ.get("CONTENT_LENGTH", "0") or "0")
        raw = environ["wsgi.input"].read(size) if size else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise InvalidRequestError(f"Invalid JSON body: {exc.msg}") from exc
        if not isinstance(body, dict):
            raise InvalidRequestError("JSON body must be an object")
        return body

    def _require_non_empty(self, body: dict, *keys: str) -> None:
        missing = [key for key in keys if not str(body.get(key, "")).strip()]
        if missing:
            raise InvalidRequestError(f"Missing required field(s): {', '.join(missing)}")

    def _parse_float(self, value, *, field: str, default: float) -> float:
        if value in (None, ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidRequestError(f"Field '{field}' must be a number") from exc

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        query = parse_qs(environ.get("QUERY_STRING", ""))

        status = "200 OK"
        payload = None

        try:
            if method == "OPTIONS":
                payload = {"ok": True, "data": None, "meta": {"path": path, "preflight": True}, "error": None}
            elif path == "/api/summary" and method == "GET":
                payload = {"ok": True, "data": self.api.layer_summary(), "meta": {}, "error": None}
            elif path == "/api/semantic-overview" and method == "GET":
                limit = int(query.get("limit", ["5"])[0] or "5")
                payload = self.api.semantic_overview_response(limit=limit)
            elif path == "/api/layer" and method == "GET":
                layer = query.get("layer", [""])[0]
                payload = self.api.list_layer_response(layer)
            elif path == "/api/graph/refresh" and method == "POST":
                payload = self.api.refresh_graph_response()
            elif path == "/api/record" and method == "GET":
                layer = query.get("layer", [""])[0]
                record_id = query.get("id", [""])[0]
                payload = self.api.get_record_response(layer, record_id)
            elif path == "/api/inspect" and method == "GET":
                q = query.get("q", [""])[0]
                payload = self.api.inspect_query_response(q)
            elif path == "/api/filter" and method == "GET":
                layer = query.get("layer", [""])[0]
                text = query.get("text", [""])[0]
                status_filter = query.get("status", [None])[0]
                payload = self.api.filter_layer_response(layer, text=text, status=status_filter)
            elif path == "/api/migration-preview" and method == "GET":
                source_layer = query.get("source_layer", [""])[0]
                record_id = query.get("id", [""])[0]
                target_layer = query.get("target_layer", [""])[0]
                new_id = query.get("new_id", [None])[0]
                payload = self.api.migration_preview_response(source_layer, record_id, target_layer, new_id=new_id)
            elif path == "/api/report" and method == "GET":
                name = query.get("name", ["memory_v2_realish_baseline"])[0]
                payload = latest_report_response(self.api.workspace_root, report_name=name)
            elif path == "/api/governance-report" and method == "GET":
                payload = self.api.governance_report_response()
            elif path == "/api/governance-report/write" and method == "POST":
                payload = self.api.write_governance_report_response()
            elif path == "/api/memory-bootstrap" and method == "POST":
                payload = self.api.bootstrap_core_memory_records_response()
            elif path == "/api/memory-bootstrap/write" and method == "POST":
                payload = self.api.write_memory_bootstrap_report_response()
            elif path == "/api/candidate-drafts" and method == "GET":
                payload = self.api.generate_candidate_drafts_response()
            elif path == "/api/candidate-draft/preview" and method == "POST":
                body = self._read_json_body(environ)
                payload = self.api.preview_candidate_draft_response(body)
            elif path == "/api/candidate-draft/apply" and method == "POST":
                body = self._read_json_body(environ)
                supersede_conflicts = str(query.get("supersede_conflicts", ["false"])[0]).lower() in {"1", "true", "yes"}
                merge_existing = str(query.get("merge_existing", ["true"])[0]).lower() in {"1", "true", "yes"}
                payload = self.api.apply_candidate_draft_response(body, supersede_conflicts=supersede_conflicts, merge_existing=merge_existing)
            elif path == "/api/supersede" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "layer", "record_id", "superseded_by")
                payload = self.api.apply_supersede_response(
                    layer=body.get("layer", ""),
                    record_id=body.get("record_id", ""),
                    superseded_by=body.get("superseded_by", ""),
                )
            elif path == "/api/batch-governance" and method == "POST":
                body = self._read_json_body(environ)
                auto_apply_safe = bool(body.get("auto_apply_safe", True))
                refresh_graph = bool(body.get("refresh_graph", True))
                payload = self.api.run_batch_governance_response(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
            elif path == "/api/batch-governance/write" and method == "POST":
                body = self._read_json_body(environ)
                auto_apply_safe = bool(body.get("auto_apply_safe", True))
                refresh_graph = bool(body.get("refresh_graph", True))
                payload = self.api.write_batch_governance_report_response(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
            elif path == "/api/migration-candidate" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "candidate_id", "source_layer", "source_id", "target_layer", "summary")
                payload = self.api.create_migration_candidate_response(
                    body.get("candidate_id", ""),
                    source_layer=body.get("source_layer", ""),
                    source_id=body.get("source_id", ""),
                    target_layer=body.get("target_layer", ""),
                    summary=body.get("summary", ""),
                    confidence=self._parse_float(body.get("confidence"), field="confidence", default=0.5),
                    target_id=body.get("target_id"),
                )
            elif path == "/api/model-profile" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "category", "name")
                category = body.get("category", "embedding")
                name = body.get("name", "")
                record = {
                    "provider": body.get("provider", ""),
                    "model": body.get("model", ""),
                    "base_url": body.get("base_url"),
                    "api_key_ref": body.get("api_key_ref"),
                    "notes": body.get("notes"),
                }
                payload = self.api.upsert_model_profile_response(category, name, record)
            elif path == "/api/skill" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "skill_id")
                skill_id = body.get("skill_id", "")
                record = {
                    "title": body.get("title", ""),
                    "summary": body.get("summary", ""),
                    "installed": bool(body.get("installed", False)),
                    "quality_score": body.get("quality_score", 0.0),
                    "evolution_status": body.get("evolution_status", "active"),
                    "proposed_by_model": body.get("proposed_by_model"),
                }
                payload = self.api.upsert_skill_response(skill_id, record)
            elif path == "/api/preference" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "key")
                key = body.get("key", "")
                record = {
                    "value": body.get("value"),
                    "value_type": body.get("value_type", "string"),
                    "notes": body.get("notes"),
                    "strength": body.get("strength", 0.5),
                    "aliases": body.get("aliases", []),
                    "tags": body.get("tags", []),
                    "status": body.get("status", "active"),
                }
                payload = self.api.upsert_preference_response(key, record)
            elif path == "/api/task" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "task_id")
                task_id = body.get("task_id", "")
                record = {
                    "title": body.get("title", ""),
                    "summary": body.get("summary", ""),
                    "next_action": body.get("next_action"),
                    "priority": body.get("priority", "medium"),
                    "related_entities": body.get("related_entities", []),
                    "state": body.get("state", "active"),
                    "aliases": body.get("aliases", []),
                    "tags": body.get("tags", []),
                    "importance": body.get("importance", "medium"),
                }
                payload = self.api.upsert_task_response(task_id, record)
            elif path == "/api/episode" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "episode_id")
                episode_id = body.get("episode_id", "")
                record = {
                    "title": body.get("title", ""),
                    "summary": body.get("summary", ""),
                    "status": body.get("status", "active"),
                    "task_ids": body.get("task_ids", []),
                    "source_refs": body.get("source_refs", []),
                    "aliases": body.get("aliases", []),
                    "tags": body.get("tags", []),
                    "importance": body.get("importance", "medium"),
                }
                payload = self.api.upsert_episode_response(episode_id, record)
            elif path == "/api/skill-proposal" and method == "POST":
                body = self._read_json_body(environ)
                self._require_non_empty(body, "proposal_id")
                proposal_id = body.get("proposal_id", "")
                record = {
                    "skill_id": body.get("skill_id"),
                    "title": body.get("title", ""),
                    "summary": body.get("summary", ""),
                    "status": body.get("status", "pending"),
                    "proposed_by_model": body.get("proposed_by_model"),
                    "source_task_ids": body.get("source_task_ids", []),
                }
                payload = self.api.upsert_record("skill_proposals", proposal_id, record)
                payload = {"ok": True, "data": payload, "meta": {"proposal_id": proposal_id}, "error": None}
            else:
                status = "404 Not Found"
                payload = {"ok": False, "data": None, "meta": {}, "error": {"code": "not_found", "message": f"Unknown path: {path}"}}
            if status == "200 OK" and payload and not payload.get("ok", True):
                error_code = (payload.get("error") or {}).get("code")
                if error_code == "not_found" or str(error_code).endswith("_not_found"):
                    status = "404 Not Found"
                elif error_code and error_code.endswith("_failed"):
                    status = "400 Bad Request"
        except InvalidRequestError as e:
            status = "400 Bad Request"
            payload = err(str(e), code="invalid_request")
            if "JSON body" in str(e):
                payload = err(str(e), code="invalid_json")
        except Exception as e:
            status = "500 Internal Server Error"
            payload = {"ok": False, "data": None, "meta": {}, "error": {"code": "server_error", "message": str(e)}}

        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        headers.extend(self._cors_headers(environ))
        start_response(status, headers)
        return [body]


def serve(workspace_root: Path, host: str = "127.0.0.1", port: int = 8765):
    app = AdminHttpApp(workspace_root)
    httpd = make_server(host, port, app, server_class=ThreadedWSGIServer)
    print(f"OpenClaw Memory admin HTTP listening on http://{host}:{port}")
    httpd.serve_forever()
