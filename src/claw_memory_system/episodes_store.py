from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class EpisodesStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "episodes.v1",
                "updated_at": now_iso(),
                "episodes": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get(self, episode_id: str) -> dict | None:
        return self.load().get("episodes", {}).get(episode_id)

    def list(self) -> dict[str, dict]:
        return self.load().get("episodes", {})

    def upsert(self, episode_id: str, record: dict) -> dict:
        data = self.load()
        episodes = data.setdefault("episodes", {})
        current = episodes.get(episode_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("episode_id", episode_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("status", "active")
        episodes[episode_id] = record
        self.save(data)
        return record
