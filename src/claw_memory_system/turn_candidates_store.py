from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class TurnCandidatesStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "turn-candidates.v1",
                "updated_at": now_iso(),
                "candidates": [],
            }
        data = json.loads(self.path.read_text())
        if not isinstance(data.get("candidates"), list):
            data["candidates"] = []
        return data

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def list(self) -> list[dict]:
        return self.load().get("candidates", [])

    def append(self, record: dict) -> dict:
        data = self.load()
        items = data.setdefault("candidates", [])
        record = dict(record)
        record.setdefault("created_at", now_iso())
        items.append(record)
        self.save(data)
        return record
