from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from .turn_summary_synth import synthesize_summary


@dataclass
class PostTurnClassifier:
    workspace_root: Path

    def classify(self, *, user_text: str, assistant_text: str = "", tool_summary: str = "") -> dict[str, Any]:
        text = "\n".join(part for part in [user_text, assistant_text, tool_summary] if str(part).strip())
        lowered = text.lower()
        candidates: list[dict[str, Any]] = []

        if any(token in lowered for token in ["以后", "默认", "优先", "不要再", "always", "prefer ", "以后都"]):
            candidates.append({
                "layer": "preferences",
                "confidence": 0.9,
                "reason": "contains stable preference markers",
                "summary": synthesize_summary("preferences", user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary),
            })

        if any(token in lowered for token in ["时间", "路径", "地址", "workspace", "schedule", "mirror", "token file", "发送时间", "镜像"]):
            candidates.append({
                "layer": "facts",
                "confidence": 0.82,
                "reason": "contains fact/config markers",
                "summary": synthesize_summary("facts", user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary),
            })

        if any(token in lowered for token in ["继续", "优化", "修复", "待办", "下一步", "阻塞", "todo", "fix ", "继续做"]):
            candidates.append({
                "layer": "tasks",
                "confidence": 0.78,
                "reason": "contains ongoing task markers",
                "summary": synthesize_summary("tasks", user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary),
            })

        if any(token in lowered for token in ["因为", "改成", "关闭", "切换", "修复了", "决定", "migrate", "disabled"]):
            candidates.append({
                "layer": "episodes",
                "confidence": 0.72,
                "reason": "contains event/decision markers",
                "summary": synthesize_summary("episodes", user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary),
            })

        candidates = sorted(candidates, key=lambda item: item["confidence"], reverse=True)

        if not candidates:
            return {
                "schema_version": "post-turn-classifier.v1",
                "should_store": False,
                "mode": "ignore",
                "candidates": [],
            }

        max_conf = max(item["confidence"] for item in candidates)
        mode = "direct" if max_conf >= 0.88 else "drafts" if max_conf >= 0.7 else "daily_only"
        return {
            "schema_version": "post-turn-classifier.v1",
            "should_store": True,
            "mode": mode,
            "candidates": candidates,
        }



def classify_turn(workspace_root: Path, *, user_text: str, assistant_text: str = "", tool_summary: str = "") -> dict[str, Any]:
    return PostTurnClassifier(workspace_root).classify(user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary)
