from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from .post_turn_classifier import PostTurnClassifier
from .turn_candidates_store import TurnCandidatesStore
from .candidate_dedupe import dedupe_key_for_candidate


@dataclass
class TurnCandidateBridge:
    workspace_root: Path
    queue: TurnCandidatesStore
    min_confidence: float = 0.88

    @classmethod
    def from_workspace(cls, workspace_root: Path, *, min_confidence: float = 0.88) -> "TurnCandidateBridge":
        root = workspace_root / "memory-system"
        return cls(
            workspace_root=workspace_root,
            queue=TurnCandidatesStore(root / "stores" / "v2" / "turn_candidates.json"),
            min_confidence=min_confidence,
        )

    def classify_and_queue(self, *, user_text: str, assistant_text: str = "", tool_summary: str = "") -> dict[str, Any]:
        classifier = PostTurnClassifier(self.workspace_root)
        result = classifier.classify(user_text=user_text, assistant_text=assistant_text, tool_summary=tool_summary)
        queued = []
        existing = self.queue.list()
        seen = {str(item.get("dedupe_key", "")) for item in existing}
        for item in result.get("candidates", []):
            confidence = float(item.get("confidence", 0) or 0)
            if confidence < self.min_confidence:
                continue
            record = {
                "target_layer": item.get("layer"),
                "summary": item.get("summary"),
                "confidence": item.get("confidence"),
                "reason": item.get("reason"),
                "source": "post-turn-classifier",
                "status": "pending",
                "user_text": user_text,
                "assistant_text": assistant_text,
                "tool_summary": tool_summary,
                "suggested_id": self._suggested_id(str(item.get("layer", "")), str(item.get("summary", ""))),
            }
            record["dedupe_key"] = dedupe_key_for_candidate(record)
            if record["dedupe_key"] in seen:
                continue
            seen.add(record["dedupe_key"])
            queued.append(self.queue.append(record))
        return {
            "schema_version": "turn-candidate-bridge.v1",
            "classification": result,
            "queued_count": len(queued),
            "queued": queued,
        }

    def _suggested_id(self, layer: str, summary: str) -> str:
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", summary.lower()).strip("-._")
        slug = slug[:60] if len(slug) > 60 else slug
        if not slug:
            slug = "candidate"
        if layer == "preferences":
            return f"pref.{slug}"
        if layer == "facts":
            return f"fact.{slug}"
        if layer == "tasks":
            return f"task.{slug}"
        if layer == "episodes":
            return f"episode.{slug}"
        return slug
