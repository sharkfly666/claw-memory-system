from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class SkillsStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "skills.v1",
                "updated_at": now_iso(),
                "skills": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get(self, skill_id: str) -> dict | None:
        return self.load().get("skills", {}).get(skill_id)

    def list(self) -> dict[str, dict]:
        return self.load().get("skills", {})

    def upsert(self, skill_id: str, record: dict) -> dict:
        data = self.load()
        skills = data.setdefault("skills", {})
        current = skills.get(skill_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("skill_id", skill_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("installed", False)
        record.setdefault("evolution_status", "active")
        skills[skill_id] = record
        self.save(data)
        return record
