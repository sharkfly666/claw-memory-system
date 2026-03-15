from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .facts_store import now_iso


@dataclass
class TasksStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "tasks.v1",
                "updated_at": now_iso(),
                "tasks": {},
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get(self, task_id: str) -> dict | None:
        return self.load().get("tasks", {}).get(task_id)

    def list(self) -> dict[str, dict]:
        return self.load().get("tasks", {})

    def upsert(self, task_id: str, record: dict) -> dict:
        data = self.load()
        tasks = data.setdefault("tasks", {})
        current = tasks.get(task_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("task_id", task_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        record.setdefault("last_active_at", now_iso())
        record.setdefault("state", "active")
        tasks[task_id] = record
        self.save(data)
        return record
