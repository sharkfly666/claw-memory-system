from __future__ import annotations

from typing import Any
import re


def queued_candidate_to_draft(candidate: dict[str, Any]) -> dict[str, Any]:
    layer = str(candidate.get("target_layer", "")).strip()
    suggested_id = str(candidate.get("suggested_id", "")).strip() or _fallback_id(layer, str(candidate.get("summary", "")))
    summary = str(candidate.get("summary", "")).strip()
    reason = str(candidate.get("reason", "")).strip()
    confidence = candidate.get("confidence")
    user_text = str(candidate.get("user_text", "")).strip()

    if layer == "preferences":
        record = {
            "summary": _clean_summary(summary),
            "scope": "global",
            "importance": "high" if (isinstance(confidence, (int, float)) and confidence >= 0.88) else "medium",
            "status": "active",
            "aliases": [user_text] if user_text else [],
            "tags": ["preference", "autocaptured"],
            "evidence": "turn-candidate-bridge",
            "notes": reason,
        }
    elif layer == "tasks":
        record = {
            "title": _title("任务", summary),
            "summary": _clean_summary(summary),
            "goal": "Review and continue this ongoing task.",
            "next_step": "Confirm scope and continue execution.",
            "blockers": [],
            "priority": "medium",
            "related_entities": _extract_entities(user_text or summary),
            "aliases": [user_text] if user_text else [],
            "tags": ["task", "autocaptured"],
            "importance": "medium",
            "state": "active",
            "owner_scope": "global",
        }
    elif layer == "episodes":
        record = {
            "title": _title("事件", summary),
            "summary": _clean_summary(summary),
            "episode_type": "autocaptured",
            "aliases": [user_text] if user_text else [],
            "tags": ["episode", "autocaptured"],
            "importance": "medium",
            "status": "active",
            "source_refs": ["turn-candidate-bridge"],
        }
    else:
        record = {
            "summary": _clean_summary(summary),
            "aliases": [user_text] if user_text else [],
            "tags": ["autocaptured"],
            "status": "active",
        }

    return {
        "candidate": candidate,
        "target_layer": layer,
        "target_id": suggested_id,
        "record": record,
    }


def _clean_summary(text: str) -> str:
    value = str(text or "").strip()
    value = re.sub(r"^(偏好候选|事实候选|任务候选|事件候选)：", "", value)
    return value.strip()


def _fallback_id(layer: str, summary: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", summary.lower()).strip("-._") or "candidate"
    slug = slug[:60] if len(slug) > 60 else slug
    prefix = {"preferences": "pref", "tasks": "task", "episodes": "episode", "facts": "fact"}.get(layer, "candidate")
    return f"{prefix}.{slug}"


def _title(prefix: str, summary: str) -> str:
    cleaned = _clean_summary(summary)
    return f"{prefix}：{cleaned[:80]}"


def _extract_entities(text: str) -> list[str]:
    lowered = text.lower()
    entities = []
    for token in ["github", "daily-briefing", "feishu", "memory", "pansou"]:
        if token in lowered:
            entities.append(token)
    return entities
