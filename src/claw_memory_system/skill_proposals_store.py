from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class SkillProposalsStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "skill-proposals.v1",
                "updated_at": now_iso(),
                "proposals": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def list(self) -> dict[str, dict]:
        return self.load().get("proposals", {})

    def get(self, proposal_id: str) -> dict | None:
        return self.load().get("proposals", {}).get(proposal_id)

    def upsert(self, proposal_id: str, record: dict) -> dict:
        data = self.load()
        proposals = data.setdefault("proposals", {})
        current = proposals.get(proposal_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("proposal_id", proposal_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("status", "pending")
        proposals[proposal_id] = record
        self.save(data)
        return record
