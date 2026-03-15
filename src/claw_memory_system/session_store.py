from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class SessionStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "session.v1",
                "updated_at": now_iso(),
                "sessions": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get(self, session_key: str) -> dict | None:
        return self.load().get("sessions", {}).get(session_key)

    def list(self) -> dict[str, dict]:
        return self.load().get("sessions", {})

    def upsert(self, session_key: str, record: dict) -> dict:
        data = self.load()
        sessions = data.setdefault("sessions", {})
        current = sessions.get(session_key)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("session_key", session_key)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("status", "active")
        sessions[session_key] = record
        self.save(data)
        return record
