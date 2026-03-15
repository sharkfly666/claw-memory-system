from __future__ import annotations

import re


def synthesize_summary(layer: str, *, user_text: str = "", assistant_text: str = "", tool_summary: str = "") -> str:
    user = _clean(user_text)
    assistant = _clean(assistant_text)
    tool = _clean(tool_summary)

    if layer == "preferences":
        if user:
            return user
        return assistant or tool or "偏好候选"
    if layer == "facts":
        if user:
            return user
        return assistant or tool or "事实候选"
    if layer == "tasks":
        if user:
            return user
        return assistant or tool or "任务候选"
    if layer == "episodes":
        parts = [part for part in [user, assistant, tool] if part]
        return "；".join(parts[:2]) if parts else "事件候选"
    return user or assistant or tool or "候选"


def _clean(text: str) -> str:
    value = re.sub(r"\s+", " ", str(text or "").strip())
    return value
