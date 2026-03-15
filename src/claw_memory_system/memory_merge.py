from __future__ import annotations

from copy import deepcopy
from typing import Any

from .record_quality import better_summary, normalize_record


def _dedupe_list(values: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for value in values:
        key = str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _pick_better_text(old: Any, new: Any) -> Any:
    old_text = str(old or "").strip()
    new_text = str(new or "").strip()
    if not old_text:
        return new
    if not new_text:
        return old
    return new if len(new_text) >= len(old_text) else old


def merge_record(existing: dict[str, Any] | None, incoming: dict[str, Any], *, layer: str) -> dict[str, Any]:
    current = deepcopy(existing or {})
    merged = deepcopy(current)

    for field in ["notes", "goal", "next_step", "decision", "impact", "title"]:
        if field in incoming:
            merged[field] = _pick_better_text(current.get(field), incoming.get(field))

    if "summary" in incoming:
        merged["summary"] = better_summary(current.get("summary"), incoming.get("summary"))

    for field in ["aliases", "tags", "related_entities", "task_ids", "related_fact_keys", "related_task_ids", "blockers", "source_refs"]:
        old_values = current.get(field, []) if isinstance(current.get(field), list) else []
        new_values = incoming.get(field, []) if isinstance(incoming.get(field), list) else []
        if old_values or new_values:
            merged[field] = _dedupe_list([*old_values, *new_values])

    for field in ["scope", "status", "state", "episode_type", "owner_scope", "value", "value_type", "superseded_by"]:
        if field in incoming and incoming.get(field) not in (None, ""):
            merged[field] = incoming.get(field)

    importance_rank = {"low": 1, "medium": 2, "high": 3}
    old_importance = str(current.get("importance", "medium"))
    new_importance = str(incoming.get("importance", "medium"))
    if importance_rank.get(new_importance, 2) >= importance_rank.get(old_importance, 2):
        merged["importance"] = new_importance
    else:
        merged["importance"] = old_importance

    for key, value in incoming.items():
        if key in merged:
            continue
        merged[key] = deepcopy(value)

    if layer == "preferences":
        merged.setdefault("status", current.get("status", "active"))
    if layer == "tasks":
        merged.setdefault("state", current.get("state", "active"))
    if layer == "episodes":
        merged.setdefault("status", current.get("status", "active"))

    return normalize_record(merged, layer=layer)
