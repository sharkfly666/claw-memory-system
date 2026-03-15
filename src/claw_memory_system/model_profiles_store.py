from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class ModelProfilesStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "models.v1",
                "updated_at": now_iso(),
                "profiles": {
                    "embedding": [],
                    "memory": [],
                    "summarization": [],
                    "skill_evolution": [],
                },
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def list(self, category: str | None = None) -> dict | list[dict]:
        profiles = self.load().get("profiles", {})
        if category is None:
            return profiles
        return profiles.get(category, [])

    def get(self, category: str, name: str) -> dict | None:
        profiles = self.load().get("profiles", {}).get(category, [])
        return next((item for item in profiles if item.get("name") == name), None)

    def upsert(self, category: str, name: str, record: dict) -> dict:
        data = self.load()
        profiles = data.setdefault("profiles", {}).setdefault(category, [])
        current = next((item for item in profiles if item.get("name") == name), None)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("name", name)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        if current:
            profiles[:] = [item for item in profiles if item.get("name") != name]
        profiles.append(record)
        self.save(data)
        return record
