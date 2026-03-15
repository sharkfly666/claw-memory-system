from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from .facts_store import FactsStore
from .memory_governance import MemoryGovernance
from .preferences_store import PreferencesStore
from .tasks_store import TasksStore
from .episodes_store import EpisodesStore


@dataclass
class MemoryCandidateDrafts:
    workspace_root: Path
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "MemoryCandidateDrafts":
        root = workspace_root / "memory-system"
        return cls(
            workspace_root=workspace_root,
            facts=FactsStore(root / "facts" / "facts.json", root / "facts" / "facts.history.jsonl"),
            preferences=PreferencesStore(root / "stores" / "v2" / "preferences.json"),
            tasks=TasksStore(root / "stores" / "v2" / "tasks.json"),
            episodes=EpisodesStore(root / "stores" / "v2" / "episodes.json"),
        )

    def generate(self) -> dict[str, Any]:
        governance = MemoryGovernance(
            workspace_root=self.workspace_root,
            facts=self.facts,
            preferences=self.preferences,
            tasks=self.tasks,
            episodes=self.episodes,
        )
        report = governance.build_report()
        drafts = []
        for candidate in report.get("migration_candidates", []):
            draft = self._draft_for_candidate(candidate)
            if draft:
                drafts.append(draft)
        return {
            "schema_version": "memory-candidate-drafts.v1",
            "workspace_root": str(self.workspace_root),
            "count": len(drafts),
            "drafts": drafts,
        }

    def _draft_for_candidate(self, candidate: dict[str, Any]) -> dict[str, Any] | None:
        layer = candidate.get("suggested_layer")
        source = str(candidate.get("source", ""))
        suggested_id = str(candidate.get("suggested_id", "")).strip() or self._fallback_id(layer, source)
        if layer == "preferences":
            return {
                "candidate": candidate,
                "target_layer": "preferences",
                "target_id": suggested_id,
                "record": self._preference_record(candidate),
            }
        if layer == "tasks":
            return {
                "candidate": candidate,
                "target_layer": "tasks",
                "target_id": suggested_id,
                "record": self._task_record(candidate),
            }
        if layer == "episodes":
            return {
                "candidate": candidate,
                "target_layer": "episodes",
                "target_id": suggested_id,
                "record": self._episode_record(candidate),
            }
        return None

    def _preference_record(self, candidate: dict[str, Any]) -> dict[str, Any]:
        source = str(candidate.get("source", ""))
        basis = self._source_basis(source)
        return {
            "summary": f"待确认：从 {basis} 提炼出的长期偏好候选。",
            "scope": "global",
            "importance": "medium",
            "status": "active",
            "aliases": [self._short_alias(basis)],
            "tags": self._tags_for_source(source, fallback=["candidate", "preference"]),
            "evidence": basis,
            "notes": candidate.get("reason"),
        }

    def _task_record(self, candidate: dict[str, Any]) -> dict[str, Any]:
        source = str(candidate.get("source", ""))
        basis = self._source_basis(source)
        title = self._title_from_source(basis, prefix="待确认任务")
        return {
            "title": title,
            "summary": f"待确认：从 {basis} 提炼出的任务候选。",
            "goal": "确认该候选是否应成为长期任务，并补齐状态/下一步。",
            "next_step": "Review candidate and decide whether to keep as active task.",
            "blockers": [],
            "priority": "medium",
            "related_entities": self._related_entities_from_source(source),
            "aliases": [self._short_alias(basis)],
            "tags": self._tags_for_source(source, fallback=["candidate", "task"]),
            "importance": "medium",
            "state": "active",
            "owner_scope": "global",
        }

    def _episode_record(self, candidate: dict[str, Any]) -> dict[str, Any]:
        source = str(candidate.get("source", ""))
        basis = self._source_basis(source)
        title = self._title_from_source(basis, prefix="待确认事件")
        return {
            "title": title,
            "summary": f"待确认：从 {basis} 提炼出的事件/决策候选。",
            "episode_type": "candidate",
            "decision": None,
            "impact": None,
            "related_fact_keys": self._fact_refs_from_source(source),
            "related_task_ids": self._task_refs_from_source(source),
            "aliases": [self._short_alias(basis)],
            "tags": self._tags_for_source(source, fallback=["candidate", "episode"]),
            "importance": "medium",
            "status": "active",
            "source_refs": [basis],
        }

    def _source_basis(self, source: str) -> str:
        if source.startswith("fact:"):
            return source
        path = Path(source)
        if path.suffix.lower() == ".md":
            return path.name
        return source

    def _fallback_id(self, layer: str, source: str) -> str:
        stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", self._source_basis(source).lower()).strip("-._") or "candidate"
        return f"{layer.rstrip('s')}.{stem}"

    def _short_alias(self, basis: str) -> str:
        text = basis.replace(".md", "").replace("fact:", "").strip()
        return text[:48] if len(text) > 48 else text

    def _title_from_source(self, basis: str, *, prefix: str) -> str:
        clean = basis.replace(".md", "").replace("fact:", "").replace("_", " ")
        return f"{prefix}：{clean}"

    def _tags_for_source(self, source: str, *, fallback: list[str]) -> list[str]:
        tags = list(fallback)
        lower = source.lower()
        for token, tag in [
            ("pansou", "pansou"),
            ("daily-briefing", "daily-briefing"),
            ("memory", "memory"),
            ("feishu", "feishu"),
        ]:
            if token in lower and tag not in tags:
                tags.append(tag)
        return tags

    def _related_entities_from_source(self, source: str) -> list[str]:
        lower = source.lower()
        entities = []
        for token in ["pansou", "daily-briefing", "memory", "feishu"]:
            if token in lower:
                entities.append(token)
        return entities

    def _fact_refs_from_source(self, source: str) -> list[str]:
        if source.startswith("fact:"):
            return [source.split(":", 1)[1]]
        return []

    def _task_refs_from_source(self, source: str) -> list[str]:
        lower = source.lower()
        refs = []
        if "daily-briefing" in lower:
            refs.append("task.daily-briefing-stability")
        if "memory" in lower:
            refs.append("task.claw-memory-layering")
        return refs
