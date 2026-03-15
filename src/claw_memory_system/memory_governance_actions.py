from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import copy

from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .preferences_store import PreferencesStore
from .tasks_store import TasksStore


@dataclass
class MemoryGovernanceActions:
    workspace_root: Path
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "MemoryGovernanceActions":
        root = workspace_root / "memory-system"
        return cls(
            workspace_root=workspace_root,
            facts=FactsStore(root / "facts" / "facts.json", root / "facts" / "facts.history.jsonl"),
            preferences=PreferencesStore(root / "stores" / "v2" / "preferences.json"),
            tasks=TasksStore(root / "stores" / "v2" / "tasks.json"),
            episodes=EpisodesStore(root / "stores" / "v2" / "episodes.json"),
        )

    def preview_draft_application(self, draft: dict[str, Any]) -> dict[str, Any]:
        layer = str(draft.get("target_layer", "")).strip()
        target_id = str(draft.get("target_id", "")).strip()
        record = draft.get("record", {})
        if layer not in {"preferences", "tasks", "episodes"}:
            raise KeyError(f"Unsupported draft target layer: {layer}")
        if not target_id or not isinstance(record, dict):
            raise ValueError("draft must include target_id and record object")

        existing = self._get_existing(layer, target_id)
        suggestions: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []

        if existing:
            conflicts.append({
                "type": "same_id_exists",
                "layer": layer,
                "target_id": target_id,
                "existing_status": existing.get("status") or existing.get("state", "active"),
            })
            suggestions.append({
                "action": "merge_or_update_existing",
                "target_id": target_id,
            })

        related_active = self._related_active_records(layer, target_id)
        for related_id, related_record in related_active.items():
            if related_id == target_id:
                continue
            conflicts.append({
                "type": "related_active_record",
                "layer": layer,
                "record_id": related_id,
                "status": related_record.get("status") or related_record.get("state", "active"),
            })
            suggestions.append({
                "action": "supersede_existing",
                "layer": layer,
                "record_id": related_id,
                "superseded_by": target_id,
            })

        if not conflicts:
            suggestions.append({
                "action": "apply_directly",
                "layer": layer,
                "target_id": target_id,
            })

        return {
            "target_layer": layer,
            "target_id": target_id,
            "conflicts": conflicts,
            "suggestions": suggestions,
            "existing": existing,
            "draft": draft,
        }

    def apply_supersede(self, *, layer: str, record_id: str, superseded_by: str) -> dict[str, Any]:
        if layer == "preferences":
            record = copy.deepcopy(self.preferences.get(record_id) or {})
            if not record:
                raise KeyError(f"Preference not found: {record_id}")
            record["status"] = "superseded"
            record["superseded_by"] = superseded_by
            return self.preferences.upsert(record_id, record)
        if layer == "tasks":
            record = copy.deepcopy(self.tasks.get(record_id) or {})
            if not record:
                raise KeyError(f"Task not found: {record_id}")
            record["state"] = "superseded"
            record["superseded_by"] = superseded_by
            return self.tasks.upsert(record_id, record)
        if layer == "episodes":
            record = copy.deepcopy(self.episodes.get(record_id) or {})
            if not record:
                raise KeyError(f"Episode not found: {record_id}")
            record["status"] = "superseded"
            record["superseded_by"] = superseded_by
            return self.episodes.upsert(record_id, record)
        if layer == "facts":
            record = copy.deepcopy(self.facts.get_fact(record_id) or {})
            if not record:
                raise KeyError(f"Fact not found: {record_id}")
            record["status"] = "superseded"
            record["superseded_by"] = superseded_by
            return self.facts.set_fact(record_id, record)
        raise KeyError(f"Unsupported layer for supersede: {layer}")

    def _get_existing(self, layer: str, record_id: str) -> dict[str, Any] | None:
        if layer == "preferences":
            return self.preferences.get(record_id)
        if layer == "tasks":
            return self.tasks.get(record_id)
        if layer == "episodes":
            return self.episodes.get(record_id)
        return None

    def _related_active_records(self, layer: str, target_id: str) -> dict[str, dict[str, Any]]:
        stem = self._stem(target_id)
        source = self._layer_items(layer)
        related: dict[str, dict[str, Any]] = {}
        for record_id, record in source.items():
            if self._stem(record_id) != stem:
                continue
            status = record.get("status") or record.get("state", "active")
            if status == "active":
                related[record_id] = record
        return related

    def _layer_items(self, layer: str) -> dict[str, dict[str, Any]]:
        if layer == "preferences":
            return self.preferences.list()
        if layer == "tasks":
            return self.tasks.list()
        if layer == "episodes":
            return self.episodes.list()
        return {}

    def _stem(self, key: str) -> str:
        text = str(key).strip().lower()
        for sep in [".", "_", "-"]:
            if sep in text:
                parts = [part for part in text.split(sep) if part]
                if len(parts) >= 2:
                    return sep.join(parts[:2])
        return text
