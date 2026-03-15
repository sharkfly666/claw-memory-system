from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .preferences_store import PreferencesStore
from .session_store import SessionStore
from .tasks_store import TasksStore


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^0-9a-zA-Z_\-\u4e00-\u9fff]+", "-", text)
    return text.strip("-_")


def _clean_text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        normalized = _normalize_token(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(text)
    return cleaned


@dataclass
class _GraphDraft:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    _edge_keys: set[tuple[str, str, str]] = field(default_factory=set)

    def add_node(self, node_id: str, payload: dict[str, Any]) -> None:
        record = dict(payload)
        record.setdefault("node_id", node_id)
        self.nodes[node_id] = record

    def add_edge(self, source: str, relation: str, target: str, **attrs: Any) -> None:
        edge_key = (source, relation, target)
        if edge_key in self._edge_keys:
            return
        self._edge_keys.add(edge_key)
        self.edges.append({
            "source": source,
            "relation": relation,
            "target": target,
            "attrs": attrs,
        })


def _record_node(node_type: str, *, label: str, layer: str, record_id: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_type": node_type,
        "label": label,
        "layer": layer,
        "record_id": record_id,
        "status": record.get("status") or record.get("state", "active"),
        "summary": record.get("summary"),
        "notes": record.get("notes"),
        "aliases": record.get("aliases", []),
        "tags": record.get("tags", []),
        "record": dict(record),
    }


def _token_node(node_type: str, token: str, *, label: str | None = None) -> dict[str, Any]:
    return {
        "node_type": node_type,
        "label": label or token,
        "layer": "graph",
        "record_id": token,
    }


def _add_alias_and_tag_edges(draft: _GraphDraft, owner_id: str, record: dict[str, Any]) -> None:
    for alias in _clean_text_list(record.get("aliases")):
        alias_key = _normalize_token(alias)
        alias_id = f"alias:{alias_key}"
        draft.add_node(alias_id, _token_node("alias", alias_key, label=alias))
        draft.add_edge(owner_id, "has_alias", alias_id)
    for tag in _clean_text_list(record.get("tags")):
        tag_key = _normalize_token(tag)
        tag_id = f"tag:{tag_key}"
        draft.add_node(tag_id, _token_node("tag", tag_key, label=tag))
        draft.add_edge(owner_id, "tagged_with", tag_id)


def _ensure_task_node(draft: _GraphDraft, task_id: str, tasks: dict[str, dict[str, Any]]) -> str:
    node_id = f"task:{task_id}"
    if node_id in draft.nodes:
        return node_id
    task = tasks.get(task_id, {})
    draft.add_node(
        node_id,
        _record_node(
            "task",
            label=task.get("title") or task_id,
            layer="tasks",
            record_id=task_id,
            record={"task_id": task_id, **task, "placeholder": not bool(task)},
        ),
    )
    return node_id


def build_structured_graph(
    *,
    facts: FactsStore,
    preferences: PreferencesStore,
    tasks: TasksStore,
    episodes: EpisodesStore,
    sessions: SessionStore,
) -> dict[str, Any]:
    draft = _GraphDraft()
    task_records = tasks.list()

    for key, record in sorted(facts.list_facts().items()):
        node_id = f"fact:{key}"
        draft.add_node(
            node_id,
            _record_node(
                "fact",
                label=key,
                layer="facts",
                record_id=key,
                record={"key": key, **record},
            ),
        )
        _add_alias_and_tag_edges(draft, node_id, record)

    for key, record in sorted(preferences.list().items()):
        node_id = f"preference:{key}"
        draft.add_node(
            node_id,
            _record_node(
                "preference",
                label=key,
                layer="preferences",
                record_id=key,
                record={"key": key, **record},
            ),
        )
        _add_alias_and_tag_edges(draft, node_id, record)

    for task_id, record in sorted(task_records.items()):
        node_id = _ensure_task_node(draft, task_id, task_records)
        draft.add_node(
            node_id,
            _record_node(
                "task",
                label=record.get("title") or task_id,
                layer="tasks",
                record_id=task_id,
                record={"task_id": task_id, **record},
            ),
        )
        _add_alias_and_tag_edges(draft, node_id, record)
        for entity in _clean_text_list(record.get("related_entities")):
            entity_key = _normalize_token(entity)
            entity_id = f"entity:{entity_key}"
            draft.add_node(entity_id, _token_node("entity", entity_key, label=entity))
            draft.add_edge(node_id, "related_to", entity_id)

    for episode_id, record in sorted(episodes.list().items()):
        node_id = f"episode:{episode_id}"
        draft.add_node(
            node_id,
            _record_node(
                "episode",
                label=record.get("title") or episode_id,
                layer="episodes",
                record_id=episode_id,
                record={"episode_id": episode_id, **record},
            ),
        )
        _add_alias_and_tag_edges(draft, node_id, record)
        for task_id in _clean_text_list(record.get("task_ids")):
            target_id = _ensure_task_node(draft, task_id, task_records)
            draft.add_edge(node_id, "references_task", target_id)

    for session_key, record in sorted(sessions.list().items()):
        node_id = f"session:{session_key}"
        draft.add_node(
            node_id,
            _record_node(
                "session",
                label=session_key,
                layer="sessions",
                record_id=session_key,
                record={"session_key": session_key, **record},
            ),
        )
        for task_id in _clean_text_list(record.get("active_task_ids")):
            target_id = _ensure_task_node(draft, task_id, task_records)
            draft.add_edge(node_id, "tracks_task", target_id)
        for topic in _clean_text_list(record.get("active_topics")):
            topic_key = _normalize_token(topic)
            topic_id = f"entity:{topic_key}"
            draft.add_node(topic_id, _token_node("entity", topic_key, label=topic))
            draft.add_edge(node_id, "tracks_topic", topic_id)

    draft.edges.sort(key=lambda edge: (edge["source"], edge["relation"], edge["target"]))
    return {
        "schema_version": "graph.v1",
        "nodes": draft.nodes,
        "edges": draft.edges,
    }
