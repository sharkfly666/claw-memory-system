from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .api_response import ok, err
from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .graph_store import GraphStore
from .graph_builder import build_structured_graph
from .preferences_store import PreferencesStore
from .session_store import SessionStore
from .skills_store import SkillsStore
from .tasks_store import TasksStore
from .model_profiles_store import ModelProfilesStore
from .migration_candidates_store import MigrationCandidatesStore
from .skill_proposals_store import SkillProposalsStore
from .retrieval_inspector import RetrievalInspector
from .search_router import SearchRouter
from .pageindex import search_index
from .semantic_memory import SemanticMemoryAdapter, build_semantic_memory_adapter
from .memory_governance import MemoryGovernance
from .memory_migrator import MemoryMigrator
from .memory_candidate_drafts import MemoryCandidateDrafts
from .memory_governance_actions import MemoryGovernanceActions
from .memory_merge import merge_record
from .record_equivalence import records_equivalent


@dataclass
class AdminAPI:
    workspace_root: Path
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore
    skills: SkillsStore
    sessions: SessionStore
    graph: GraphStore
    models: ModelProfilesStore | None = None
    migration_candidates: MigrationCandidatesStore | None = None
    skill_proposals: SkillProposalsStore | None = None
    semantic_adapter: SemanticMemoryAdapter | None = None
    router: SearchRouter | None = None

    @staticmethod
    def _require_id(value: str, *, label: str) -> None:
        if not str(value).strip():
            raise ValueError(f"{label} is required")

    @classmethod
    def _require_non_empty_fields(cls, fields: dict[str, Any]) -> None:
        missing = [name for name, value in fields.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    @staticmethod
    def _count_records(data: Any) -> int:
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            if data and all(isinstance(value, list) for value in data.values()):
                return sum(len(value) for value in data.values())
            return len(data)
        return 0

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "AdminAPI":
        root = workspace_root / "memory-system"
        facts = FactsStore(root / "facts" / "facts.json")
        preferences = PreferencesStore(root / "stores" / "v2" / "preferences.json")
        tasks = TasksStore(root / "stores" / "v2" / "tasks.json")
        episodes = EpisodesStore(root / "stores" / "v2" / "episodes.json")
        skills = SkillsStore(root / "stores" / "v2" / "skills.json")
        sessions = SessionStore(root / "stores" / "v2" / "session.json")
        graph = GraphStore(root / "stores" / "v2" / "graph.json")
        models = ModelProfilesStore(root / "stores" / "v2" / "models.json")
        pageindex_db = root / "index" / "pageindex.sqlite"
        exact_query = lambda query, db_path=pageindex_db: search_index(db_path, query)
        semantic_adapter = build_semantic_memory_adapter(workspace_root, models)
        return cls(
            workspace_root=workspace_root,
            facts=facts,
            preferences=preferences,
            tasks=tasks,
            episodes=episodes,
            skills=skills,
            sessions=sessions,
            graph=graph,
            models=models,
            migration_candidates=MigrationCandidatesStore(root / "stores" / "v2" / "migration_candidates.json"),
            skill_proposals=SkillProposalsStore(root / "stores" / "v2" / "skill_proposals.json"),
            semantic_adapter=semantic_adapter,
            router=SearchRouter(
                facts=facts,
                preferences=preferences,
                tasks=tasks,
                episodes=episodes,
                sessions=sessions,
                graph=graph,
                vector_query=semantic_adapter.search if semantic_adapter else None,
                exact_query=exact_query,
            ),
        )

    def list_layer(self, layer: str) -> dict[str, Any] | list[dict[str, Any]]:
        if layer == "facts":
            return self.facts.list_facts()
        if layer == "preferences":
            return self.preferences.list()
        if layer == "tasks":
            return self.tasks.list()
        if layer == "episodes":
            return self.episodes.list()
        if layer == "skills":
            return self.skills.list()
        if layer == "sessions":
            return self.sessions.list()
        if layer == "graph.nodes":
            return self.graph.list_nodes()
        if layer == "graph.edges":
            return self.graph.list_edges()
        if layer == "models":
            return self.models.list() if self.models else {}
        if layer == "migration_candidates":
            return self.migration_candidates.list() if self.migration_candidates else {}
        if layer == "skill_proposals":
            return self.skill_proposals.list() if self.skill_proposals else {}
        raise KeyError(f"Unsupported layer: {layer}")

    def list_layer_response(self, layer: str) -> dict[str, Any]:
        try:
            data = self.list_layer(layer)
            count = self._count_records(data)
            return ok(data, meta={"layer": layer, "count": count})
        except Exception as e:
            return err(str(e), code="list_layer_failed", meta={"layer": layer})

    def get_record(self, layer: str, record_id: str) -> dict[str, Any] | None:
        if layer == "facts":
            return self.facts.get_fact(record_id)
        if layer == "preferences":
            return self.preferences.get(record_id)
        if layer == "tasks":
            return self.tasks.get(record_id)
        if layer == "episodes":
            return self.episodes.get(record_id)
        if layer == "skills":
            return self.skills.get(record_id)
        if layer == "sessions":
            return self.sessions.get(record_id)
        if layer == "graph.nodes":
            return self.graph.get_node(record_id)
        if layer == "models":
            if not self.models:
                return None
            if "/" in record_id:
                category, name = record_id.split("/", 1)
                return self.models.get(category, name)
            profiles = self.models.list()
            if isinstance(profiles, dict):
                for category, items in profiles.items():
                    if isinstance(items, list):
                        found = next((item for item in items if item.get("name") == record_id), None)
                        if found:
                            return found
            return None
        if layer == "migration_candidates":
            return self.migration_candidates.get(record_id) if self.migration_candidates else None
        if layer == "skill_proposals":
            return self.skill_proposals.get(record_id) if self.skill_proposals else None
        raise KeyError(f"Unsupported layer: {layer}")

    def get_record_response(self, layer: str, record_id: str) -> dict[str, Any]:
        try:
            data = self.get_record(layer, record_id)
            if data is None:
                return err("Record not found", code="not_found", meta={"layer": layer, "record_id": record_id})
            return ok(data, meta={"layer": layer, "record_id": record_id})
        except Exception as e:
            return err(str(e), code="get_record_failed", meta={"layer": layer, "record_id": record_id})

    def upsert_record(self, layer: str, record_id: str, record: dict[str, Any]) -> dict[str, Any]:
        self._require_id(record_id, label="record_id")
        if layer == "preferences":
            return self.preferences.upsert(record_id, record)
        if layer == "tasks":
            return self.tasks.upsert(record_id, record)
        if layer == "episodes":
            return self.episodes.upsert(record_id, record)
        if layer == "skills":
            return self.skills.upsert(record_id, record)
        if layer == "sessions":
            return self.sessions.upsert(record_id, record)
        if layer == "graph.nodes":
            return self.graph.upsert_node(record_id, record)
        if layer == "migration_candidates":
            return self.migration_candidates.upsert(record_id, record) if self.migration_candidates else record
        if layer == "skill_proposals":
            return self.skill_proposals.upsert(record_id, record) if self.skill_proposals else record
        raise KeyError(f"Layer does not support generic upsert: {layer}")

    def migrate_record(self, source_layer: str, record_id: str, target_layer: str, *, new_id: str | None = None) -> dict[str, Any]:
        record = self.get_record(source_layer, record_id)
        if not record:
            raise KeyError(f"Record not found: {source_layer}:{record_id}")
        target_id = new_id or record_id
        migrated = dict(record)
        migrated["migrated_from"] = {"layer": source_layer, "id": record_id}
        return self.upsert_record(target_layer, target_id, migrated)

    def create_migration_candidate(
        self,
        candidate_id: str,
        *,
        source_layer: str,
        source_id: str,
        target_layer: str,
        summary: str,
        confidence: float = 0.5,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_non_empty_fields(
            {
                "candidate_id": candidate_id,
                "source_layer": source_layer,
                "source_id": source_id,
                "target_layer": target_layer,
                "summary": summary,
            }
        )
        if not self.migration_candidates:
            raise RuntimeError("Migration candidates store is not configured")
        return self.migration_candidates.upsert(candidate_id, {
            "source_layer": source_layer,
            "source_id": source_id,
            "target_layer": target_layer,
            "target_id": target_id,
            "summary": summary,
            "confidence": confidence,
        })

    def create_migration_candidate_response(
        self,
        candidate_id: str,
        *,
        source_layer: str,
        source_id: str,
        target_layer: str,
        summary: str,
        confidence: float = 0.5,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            data = self.create_migration_candidate(
                candidate_id,
                source_layer=source_layer,
                source_id=source_id,
                target_layer=target_layer,
                summary=summary,
                confidence=confidence,
                target_id=target_id,
            )
            return ok(data, meta={"candidate_id": candidate_id})
        except Exception as e:
            return err(str(e), code="create_migration_candidate_failed", meta={"candidate_id": candidate_id})

    def upsert_model_profile_response(self, category: str, name: str, record: dict[str, Any]) -> dict[str, Any]:
        try:
            if not self.models:
                raise RuntimeError("Model profiles store is not configured")
            self._require_non_empty_fields({"category": category, "name": name})
            data = self.models.upsert(category, name, record)
            return ok(data, meta={"category": category, "name": name})
        except Exception as e:
            return err(str(e), code="upsert_model_profile_failed", meta={"category": category, "name": name})

    def upsert_skill_response(self, skill_id: str, record: dict[str, Any]) -> dict[str, Any]:
        try:
            self._require_id(skill_id, label="skill_id")
            data = self.skills.upsert(skill_id, record)
            return ok(data, meta={"skill_id": skill_id})
        except Exception as e:
            return err(str(e), code="upsert_skill_failed", meta={"skill_id": skill_id})

    def upsert_preference_response(self, key: str, record: dict[str, Any]) -> dict[str, Any]:
        try:
            self._require_id(key, label="key")
            data = self.preferences.upsert(key, record)
            return ok(data, meta={"key": key})
        except Exception as e:
            return err(str(e), code="upsert_preference_failed", meta={"key": key})

    def upsert_task_response(self, task_id: str, record: dict[str, Any]) -> dict[str, Any]:
        try:
            self._require_id(task_id, label="task_id")
            data = self.tasks.upsert(task_id, record)
            return ok(data, meta={"task_id": task_id})
        except Exception as e:
            return err(str(e), code="upsert_task_failed", meta={"task_id": task_id})

    def upsert_episode_response(self, episode_id: str, record: dict[str, Any]) -> dict[str, Any]:
        try:
            self._require_id(episode_id, label="episode_id")
            data = self.episodes.upsert(episode_id, record)
            return ok(data, meta={"episode_id": episode_id})
        except Exception as e:
            return err(str(e), code="upsert_episode_failed", meta={"episode_id": episode_id})

    def refresh_graph(self) -> dict[str, int]:
        graph_data = build_structured_graph(
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
            sessions=self.sessions,
        )
        self.graph.save(graph_data)
        return self.layer_summary()

    def refresh_graph_response(self) -> dict[str, Any]:
        try:
            data = self.refresh_graph()
            return ok(data, meta={"action": "refresh_graph"})
        except Exception as e:
            return err(str(e), code="refresh_graph_failed")

    def layer_summary(self) -> dict[str, int]:
        return {
            "facts": len(self.facts.list_facts()),
            "preferences": len(self.preferences.list()),
            "tasks": len(self.tasks.list()),
            "episodes": len(self.episodes.list()),
            "skills": len(self.skills.list()),
            "sessions": len(self.sessions.list()),
            "graph_nodes": len(self.graph.list_nodes()),
            "graph_edges": len(self.graph.list_edges()),
            "model_profiles": self._count_records(self.models.list()) if self.models else 0,
            "migration_candidates": len(self.migration_candidates.list()) if self.migration_candidates else 0,
            "skill_proposals": len(self.skill_proposals.list()) if self.skill_proposals else 0,
        }

    def semantic_overview(self, *, limit: int = 5) -> dict[str, Any]:
        if not self.semantic_adapter:
            return {
                "configured": False,
                "provider": None,
                "total_count": 0,
                "scope_counts": {},
                "category_counts": {},
                "retrieval": {},
                "recent": [],
            }
        overview = self.semantic_adapter.overview(limit=limit)
        if not isinstance(overview, dict):
            raise ValueError("Semantic adapter overview must return an object")
        return {
            "configured": True,
            "provider": overview.get("provider", self.semantic_adapter.provider),
            "total_count": int(overview.get("total_count", 0) or 0),
            "scope_counts": overview.get("scope_counts", {}) if isinstance(overview.get("scope_counts", {}), dict) else {},
            "category_counts": overview.get("category_counts", {}) if isinstance(overview.get("category_counts", {}), dict) else {},
            "retrieval": overview.get("retrieval", {}) if isinstance(overview.get("retrieval", {}), dict) else {},
            "recent": overview.get("recent", []) if isinstance(overview.get("recent", []), list) else [],
        }

    def semantic_overview_response(self, *, limit: int = 5) -> dict[str, Any]:
        try:
            data = self.semantic_overview(limit=limit)
            return ok(data, meta={"limit": limit, "provider": data.get("provider")})
        except Exception as e:
            return err(str(e), code="semantic_overview_failed", meta={"limit": limit})

    def governance_report(self) -> dict[str, Any]:
        governance = MemoryGovernance(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        return governance.build_report()

    def governance_report_response(self) -> dict[str, Any]:
        try:
            data = self.governance_report()
            return ok(data, meta={"action": "governance_report"})
        except Exception as e:
            return err(str(e), code="governance_report_failed")

    def write_governance_report(self) -> dict[str, Any]:
        governance = MemoryGovernance(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        path = governance.write_report()
        return {
            "path": str(path),
            "report": governance.build_report(),
        }

    def write_governance_report_response(self) -> dict[str, Any]:
        try:
            data = self.write_governance_report()
            return ok(data, meta={"action": "write_governance_report", "path": data.get("path")})
        except Exception as e:
            return err(str(e), code="write_governance_report_failed")

    def generate_candidate_drafts(self) -> dict[str, Any]:
        drafts = MemoryCandidateDrafts(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        return drafts.generate()

    def generate_candidate_drafts_response(self) -> dict[str, Any]:
        try:
            data = self.generate_candidate_drafts()
            return ok(data, meta={"action": "generate_candidate_drafts", "count": data.get("count", 0)})
        except Exception as e:
            return err(str(e), code="generate_candidate_drafts_failed")

    def bootstrap_core_memory_records(self) -> dict[str, Any]:
        migrator = MemoryMigrator(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        return migrator.bootstrap_core_records()

    def bootstrap_core_memory_records_response(self) -> dict[str, Any]:
        try:
            data = self.bootstrap_core_memory_records()
            return ok(data, meta={"action": "bootstrap_core_memory_records"})
        except Exception as e:
            return err(str(e), code="bootstrap_core_memory_records_failed")

    def write_memory_bootstrap_report(self) -> dict[str, Any]:
        migrator = MemoryMigrator(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        path = migrator.write_bootstrap_report()
        return {
            "path": str(path),
            "report": json.loads(Path(path).read_text(encoding="utf-8")),
        }

    def write_memory_bootstrap_report_response(self) -> dict[str, Any]:
        try:
            data = self.write_memory_bootstrap_report()
            return ok(data, meta={"action": "write_memory_bootstrap_report", "path": data.get("path")})
        except Exception as e:
            return err(str(e), code="write_memory_bootstrap_report_failed")

    def preview_candidate_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        actions = MemoryGovernanceActions(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        return actions.preview_draft_application(draft)

    def preview_candidate_draft_response(self, draft: dict[str, Any]) -> dict[str, Any]:
        try:
            data = self.preview_candidate_draft(draft)
            return ok(data, meta={"action": "preview_candidate_draft", "target_layer": draft.get("target_layer"), "target_id": draft.get("target_id")})
        except Exception as e:
            return err(str(e), code="preview_candidate_draft_failed")

    def apply_candidate_draft(self, draft: dict[str, Any], *, supersede_conflicts: bool = False, merge_existing: bool = True) -> dict[str, Any]:
        preview = self.preview_candidate_draft(draft)
        hard_conflicts = [item for item in preview.get("conflicts", []) if item.get("type") != "same_id_exists"]
        if hard_conflicts and not supersede_conflicts:
            raise ValueError("draft has conflicts; preview first or pass supersede_conflicts=true")

        if supersede_conflicts:
            actions = MemoryGovernanceActions(
                workspace_root=self.workspace_root,
                facts=self.facts,
                preferences=self.preferences,
                tasks=self.tasks,
                episodes=self.episodes,
            )
            for suggestion in preview.get("suggestions", []):
                if suggestion.get("action") == "supersede_existing":
                    actions.apply_supersede(
                        layer=str(suggestion.get("layer")),
                        record_id=str(suggestion.get("record_id")),
                        superseded_by=str(suggestion.get("superseded_by")),
                    )

        layer = str(draft.get("target_layer", "")).strip()
        record_id = str(draft.get("target_id", "")).strip()
        record = draft.get("record", {})
        if not layer or not record_id or not isinstance(record, dict):
            raise ValueError("draft must include target_layer, target_id, and record object")

        existing = preview.get("existing") if isinstance(preview.get("existing"), dict) else None
        record_to_apply = merge_record(existing, record, layer=layer) if merge_existing else record

        if records_equivalent(existing, record_to_apply):
            return {
                "applied": existing,
                "preview": preview,
                "merge_existing": merge_existing,
                "noop": True,
            }

        if layer == "preferences":
            applied = self.preferences.upsert(record_id, record_to_apply)
        elif layer == "tasks":
            applied = self.tasks.upsert(record_id, record_to_apply)
        elif layer == "episodes":
            applied = self.episodes.upsert(record_id, record_to_apply)
        else:
            raise KeyError(f"Unsupported draft target layer: {layer}")
        return {
            "applied": applied,
            "preview": preview,
            "merge_existing": merge_existing,
            "noop": False,
        }

    def apply_candidate_draft_response(self, draft: dict[str, Any], *, supersede_conflicts: bool = False, merge_existing: bool = True) -> dict[str, Any]:
        try:
            data = self.apply_candidate_draft(draft, supersede_conflicts=supersede_conflicts, merge_existing=merge_existing)
            return ok(data, meta={"action": "apply_candidate_draft", "target_layer": draft.get("target_layer"), "target_id": draft.get("target_id"), "supersede_conflicts": supersede_conflicts, "merge_existing": merge_existing})
        except Exception as e:
            return err(str(e), code="apply_candidate_draft_failed")

    def apply_supersede_response(self, *, layer: str, record_id: str, superseded_by: str) -> dict[str, Any]:
        try:
            actions = MemoryGovernanceActions(
                workspace_root=self.workspace_root,
                facts=self.facts,
                preferences=self.preferences,
                tasks=self.tasks,
                episodes=self.episodes,
            )
            data = actions.apply_supersede(layer=layer, record_id=record_id, superseded_by=superseded_by)
            return ok(data, meta={"action": "apply_supersede", "layer": layer, "record_id": record_id, "superseded_by": superseded_by})
        except Exception as e:
            return err(str(e), code="apply_supersede_failed")

    def run_batch_governance(self, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
        from .batch_governance import BatchGovernance
        runner = BatchGovernance.from_workspace(self.workspace_root)
        return runner.run(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)

    def run_batch_governance_response(self, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
        try:
            data = self.run_batch_governance(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
            return ok(data, meta={"action": "run_batch_governance", "auto_apply_safe": auto_apply_safe, "refresh_graph": refresh_graph})
        except Exception as e:
            return err(str(e), code="run_batch_governance_failed")

    def write_batch_governance_report(self, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
        from .batch_governance import BatchGovernance
        runner = BatchGovernance.from_workspace(self.workspace_root)
        path = runner.write_report(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
        return {
            "path": str(path),
            "report": json.loads(Path(path).read_text(encoding="utf-8")),
        }

    def write_batch_governance_report_response(self, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
        try:
            data = self.write_batch_governance_report(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
            return ok(data, meta={"action": "write_batch_governance_report", "path": data.get("path"), "auto_apply_safe": auto_apply_safe, "refresh_graph": refresh_graph})
        except Exception as e:
            return err(str(e), code="write_batch_governance_report_failed")

    def inspect_query(self, query: str) -> dict[str, Any]:
        if not self.router:
            self.router = SearchRouter(
                facts=self.facts,
                preferences=self.preferences,
                tasks=self.tasks,
                episodes=self.episodes,
                sessions=self.sessions,
                graph=self.graph,
                vector_query=self.semantic_adapter.search if self.semantic_adapter else None,
            )
        inspector = RetrievalInspector(self.router)
        return inspector.inspect(query)

    def inspect_query_response(self, query: str) -> dict[str, Any]:
        try:
            data = self.inspect_query(query)
            return ok(data, meta={"query": query, "route": data.get("route")})
        except Exception as e:
            return err(str(e), code="inspect_query_failed", meta={"query": query})

    def filter_layer(self, layer: str, *, text: str = "", status: str | None = None) -> list[dict[str, Any]]:
        raw = self.list_layer(layer)
        items = raw.values() if isinstance(raw, dict) else raw
        results: list[dict[str, Any]] = []
        for item in items:
            if text and text.lower() not in str(item).lower():
                continue
            if status and isinstance(item, dict) and item.get("status") != status:
                continue
            results.append(item)
        return results

    def filter_layer_response(self, layer: str, *, text: str = "", status: str | None = None) -> dict[str, Any]:
        try:
            data = self.filter_layer(layer, text=text, status=status)
            return ok(data, meta={"layer": layer, "count": len(data), "text": text, "status": status})
        except Exception as e:
            return err(str(e), code="filter_layer_failed", meta={"layer": layer, "text": text, "status": status})

    def migration_preview(self, source_layer: str, record_id: str, target_layer: str, *, new_id: str | None = None) -> dict[str, Any]:
        record = self.get_record(source_layer, record_id)
        if not record:
            raise KeyError(f"Record not found: {source_layer}:{record_id}")
        target_id = new_id or record_id
        preview = dict(record)
        preview["migrated_from"] = {"layer": source_layer, "id": record_id}
        return {
            "source_layer": source_layer,
            "source_id": record_id,
            "target_layer": target_layer,
            "target_id": target_id,
            "preview": preview,
        }

    def migration_preview_response(self, source_layer: str, record_id: str, target_layer: str, *, new_id: str | None = None) -> dict[str, Any]:
        try:
            data = self.migration_preview(source_layer, record_id, target_layer, new_id=new_id)
            return ok(data, meta={"source_layer": source_layer, "target_layer": target_layer})
        except Exception as e:
            return err(str(e), code="migration_preview_failed", meta={"source_layer": source_layer, "record_id": record_id, "target_layer": target_layer})
