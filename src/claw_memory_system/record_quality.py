from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _starts_with_candidate_marker(text: str) -> bool:
    lowered = text.lower()
    return lowered.startswith("待确认") or lowered.startswith("candidate:") or "提炼出的" in lowered or "fact:" in lowered


def score_summary(text: str) -> float:
    value = _text(text)
    if not value:
        return 0.0
    score = min(len(value) / 40.0, 2.0)
    if _starts_with_candidate_marker(value):
        score -= 1.4
    if any(token in value for token in ["用户偏好", "当前", "优先", "不要", "每天", "关闭", "修复"]):
        score += 0.8
    if len(value) >= 12:
        score += 0.4
    return score


def better_summary(existing: Any, incoming: Any) -> Any:
    old = _text(existing)
    new = _text(incoming)
    if not old:
        return incoming
    if not new:
        return existing
    return incoming if score_summary(new) >= score_summary(old) else existing


def normalize_record(record: dict[str, Any], *, layer: str) -> dict[str, Any]:
    normalized = dict(record)
    summary = _text(normalized.get("summary"))
    tags = normalized.get("tags") if isinstance(normalized.get("tags"), list) else []
    tags = [str(tag) for tag in tags if str(tag).strip()]

    if summary and not _starts_with_candidate_marker(summary):
        tags = [tag for tag in tags if tag != "candidate"]
        if layer == "preferences" and "preference" not in tags:
            tags.append("preference")
        if layer == "tasks" and "task" not in tags:
            tags.append("task")
        if layer == "episodes" and "episode" not in tags:
            tags.append("episode")

    normalized["tags"] = list(dict.fromkeys(tags))
    normalized["summary"] = summary or normalized.get("summary")
    return normalized
