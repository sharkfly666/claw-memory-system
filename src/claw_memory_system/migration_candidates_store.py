from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class MigrationCandidatesStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "migration-candidates.v1",
                "updated_at": now_iso(),
                "candidates": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def list(self) -> dict[str, dict]:
        return self.load().get("candidates", {})

    def get(self, candidate_id: str) -> dict | None:
        return self.load().get("candidates", {}).get(candidate_id)

    def upsert(self, candidate_id: str, record: dict) -> dict:
        data = self.load()
        candidates = data.setdefault("candidates", {})
        current = candidates.get(candidate_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("candidate_id", candidate_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("status", "pending")
        candidates[candidate_id] = record
        self.save(data)
        return record
