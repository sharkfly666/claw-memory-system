from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from .compat import ensure_facts_compatible


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class FactsStore:
    path: Path
    history_path: Path | None = None

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "version": "1.0",
                "updated_at": now_iso(),
                "facts": {},
            }
        ensure_facts_compatible(self.path)
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def get_fact(self, key: str) -> dict | None:
        return self.load().get("facts", {}).get(key)

    def list_facts(self) -> dict[str, dict]:
        return self.load().get("facts", {})

    def _append_history(self, key: str, old: dict) -> None:
        if not self.history_path:
            return
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "migrated_at": now_iso(),
                "key": key,
                "old": old,
            }, ensure_ascii=False) + "\n")

    def set_fact(self, key: str, fact: dict) -> dict:
        data = self.load()
        facts = data.setdefault("facts", {})
        old = facts.get(key)
        if old:
            self._append_history(key, old)
        facts[key] = fact
        self.save(data)
        return fact

    def upsert_simple(
        self,
        key: str,
        value: Any,
        *,
        value_type: str,
        category: str = "fact",
        status: str = "active",
        source: str,
        scope: str = "global",
        aliases: list[str] | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
        confidence: float = 1.0,
    ) -> dict:
        current = self.get_fact(key)
        created_at = current.get("created_at") if current else now_iso()
        fact = {
            "value": value,
            "value_type": value_type,
            "category": category,
            "status": status,
            "updated_at": now_iso(),
            "created_at": created_at,
            "last_verified": now_iso(),
            "valid_from": current.get("valid_from") if current else now_iso(),
            "valid_to": None,
            "ttl_days": current.get("ttl_days") if current else None,
            "confidence": confidence,
            "source": source,
            "scope": scope,
            "aliases": aliases or [],
            "tags": tags or [],
            "notes": notes,
            "superseded_by": None,
        }
        return self.set_fact(key, fact)
