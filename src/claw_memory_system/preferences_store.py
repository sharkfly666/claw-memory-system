from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class PreferencesStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "preferences.v1",
                "updated_at": now_iso(),
                "preferences": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get(self, key: str) -> dict | None:
        return self.load().get("preferences", {}).get(key)

    def list(self) -> dict[str, dict]:
        return self.load().get("preferences", {})

    def upsert(self, key: str, record: dict) -> dict:
        data = self.load()
        prefs = data.setdefault("preferences", {})
        current = prefs.get(key)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("key", key)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("last_verified", now_iso())
        prefs[key] = record
        self.save(data)
        return record
