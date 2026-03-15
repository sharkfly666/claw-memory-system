from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .facts_store import now_iso


@dataclass
class GraphStore:
    path: Path

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "graph.v1",
                "updated_at": now_iso(),
                "nodes": {},
                "edges": [],
            }
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def list_nodes(self) -> dict[str, dict]:
        return self.load().get("nodes", {})

    def list_edges(self) -> list[dict[str, Any]]:
        return self.load().get("edges", [])

    def get_node(self, node_id: str) -> dict | None:
        return self.load().get("nodes", {}).get(node_id)

    def upsert_node(self, node_id: str, record: dict) -> dict:
        data = self.load()
        nodes = data.setdefault("nodes", {})
        current = nodes.get(node_id)
        created_at = current.get("created_at") if current else now_iso()
        record.setdefault("node_id", node_id)
        record.setdefault("created_at", created_at)
        record["updated_at"] = now_iso()
        nodes[node_id] = record
        self.save(data)
        return record

    def add_edge(self, source: str, relation: str, target: str, **attrs: Any) -> dict:
        data = self.load()
        edge = {
            "source": source,
            "relation": relation,
            "target": target,
            "attrs": attrs,
            "created_at": now_iso(),
        }
        data.setdefault("edges", []).append(edge)
        self.save(data)
        return edge
