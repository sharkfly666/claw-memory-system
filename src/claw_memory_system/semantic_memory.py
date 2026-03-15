from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import json
import os
import subprocess

from .model_profiles_store import ModelProfilesStore


AdapterFactory = Callable[[Path, dict[str, Any]], "SemanticMemoryAdapter"]


class SemanticMemoryAdapter:
    provider = "unknown"

    def __init__(self, workspace_root: Path, profile: dict[str, Any]) -> None:
        self.workspace_root = workspace_root
        self.profile = profile

    def search(self, query: str, *, limit: int | None = None) -> list[dict]:
        raise NotImplementedError

    def overview(self, *, limit: int | None = None) -> dict[str, Any]:
        return {
            "configured": True,
            "provider": self.provider,
            "total_count": 0,
            "scope_counts": {},
            "category_counts": {},
            "retrieval": {},
            "recent": [],
        }


def _render_template(value: str, context: dict[str, Any]) -> str:
    rendered = value
    for key, item in context.items():
        rendered = rendered.replace("{" + key + "}", str(item))
    return rendered


def _load_json_payload(stdout: str, provider: str) -> Any:
    trimmed = (stdout or "").strip()
    if not trimmed:
        return []

    lines = trimmed.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index].lstrip()
        if not line:
            continue
        if line.startswith("[plugins]") or line.startswith("[gateway]"):
            continue
        if not (line.startswith("{") or line.startswith("[")):
            continue
        try:
            return json.loads("\n".join(lines[index:]))
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Invalid JSON returned by {provider}: no JSON payload found in stdout")


def _select_active_profile(profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
    enabled = [profile for profile in profiles if profile.get("enabled", True)]
    if not enabled:
        return None
    active = [profile for profile in enabled if profile.get("active")]
    if len(active) == 1:
        return active[0]
    if len(active) > 1:
        raise ValueError("Multiple active semantic memory profiles found")
    if len(enabled) == 1:
        return enabled[0]
    raise ValueError("Multiple enabled semantic memory profiles found; mark one as active")


_ADAPTER_FACTORIES: dict[str, AdapterFactory] = {}


def register_semantic_memory_adapter(provider: str, factory: AdapterFactory) -> None:
    _ADAPTER_FACTORIES[provider] = factory


def unregister_semantic_memory_adapter(provider: str) -> None:
    _ADAPTER_FACTORIES.pop(provider, None)


def build_semantic_memory_adapter(workspace_root: Path, models: ModelProfilesStore | None) -> SemanticMemoryAdapter | None:
    if not models:
        return None
    profiles = models.list("memory")
    if not isinstance(profiles, list):
        return None
    profile = _select_active_profile(profiles)
    if not profile:
        return None
    provider = str(profile.get("provider", "")).strip()
    if not provider:
        raise ValueError("Semantic memory profile is missing provider")
    factory = _ADAPTER_FACTORIES.get(provider)
    if not factory:
        raise ValueError(f"Unsupported semantic memory provider: {provider}")
    return factory(workspace_root.resolve(), profile)


@dataclass
class MemoryLanceDBProAdapter(SemanticMemoryAdapter):
    workspace_root: Path
    profile: dict[str, Any]

    provider = "memory-lancedb-pro"

    def __init__(self, workspace_root: Path, profile: dict[str, Any]) -> None:
        super().__init__(workspace_root, profile)
        self.workspace_root = workspace_root
        self.profile = profile

    def search(self, query: str, *, limit: int | None = None) -> list[dict]:
        resolved_limit = int(limit if limit is not None else self.profile.get("limit", 10))
        payload = self._run_json_command("search", query=query, limit=resolved_limit)
        if isinstance(payload, dict):
            payload = payload.get("hits", [])
        if not isinstance(payload, list):
            raise ValueError("memory-lancedb-pro search output must be a JSON list or object with hits")
        return [self._normalize_hit(item, index) for index, item in enumerate(payload, start=1)]

    def overview(self, *, limit: int | None = None) -> dict[str, Any]:
        resolved_limit = int(limit if limit is not None else self.profile.get("recent_limit", 5))
        stats_payload = self._run_json_command("stats", limit=resolved_limit)
        recent_payload = self._run_json_command("list", limit=resolved_limit)

        memory_payload = stats_payload.get("memory", {}) if isinstance(stats_payload, dict) else {}
        retrieval_payload = stats_payload.get("retrieval", {}) if isinstance(stats_payload, dict) else {}
        if not isinstance(memory_payload, dict):
            memory_payload = {}
        if not isinstance(retrieval_payload, dict):
            retrieval_payload = {}
        if not isinstance(recent_payload, list):
            raise ValueError("memory-lancedb-pro list output must be a JSON list")

        return {
            "configured": True,
            "provider": self.provider,
            "total_count": int(memory_payload.get("totalCount", 0) or 0),
            "scope_counts": self._normalize_counter_map(memory_payload.get("scopeCounts")),
            "category_counts": self._normalize_counter_map(memory_payload.get("categoryCounts")),
            "retrieval": retrieval_payload,
            "recent": [self._normalize_recent_entry(item, index) for index, item in enumerate(recent_payload, start=1)],
        }

    def _resolve_openclaw_bin(self) -> str:
        configured = str(self.profile.get("openclaw_bin", "")).strip()
        if configured:
            return configured
        env_value = str(os.environ.get("OPENCLAW_BIN", "")).strip()
        if env_value:
            return env_value
        return "openclaw"

    def _build_command(self, mode: str, context: dict[str, Any]) -> list[str]:
        override_key = {
            "search": "command",
            "stats": "stats_command",
            "list": "list_command",
        }.get(mode)
        override = self.profile.get(override_key) if override_key else None
        if override:
            if not isinstance(override, list) or not all(isinstance(item, str) for item in override):
                raise ValueError(f"Semantic memory {mode} command must be a list of strings")
            return [_render_template(item, context) for item in override]

        openclaw_bin = self._resolve_openclaw_bin()
        scope = str(self.profile.get("scope", "")).strip()
        category = str(self.profile.get("category", "")).strip()
        if mode == "search":
            argv = [openclaw_bin, "memory-pro", "search", str(context["query"]), "--json", "--limit", str(context["limit"])]
            if scope:
                argv.extend(["--scope", scope])
            if category:
                argv.extend(["--category", category])
            return argv
        if mode == "stats":
            argv = [openclaw_bin, "memory-pro", "stats", "--json"]
            if scope:
                argv.extend(["--scope", scope])
            return argv
        if mode == "list":
            argv = [openclaw_bin, "memory-pro", "list", "--json", "--limit", str(context["limit"])]
            if scope:
                argv.extend(["--scope", scope])
            if category:
                argv.extend(["--category", category])
            return argv
        raise ValueError(f"Unsupported semantic memory mode: {mode}")

    def _run_json_command(self, mode: str, *, query: str = "", limit: int = 10) -> Any:
        resolved_openclaw_bin = self._resolve_openclaw_bin()
        context = {
            "workspace": str(self.workspace_root),
            "query": query,
            "limit": limit,
            "openclaw_bin": resolved_openclaw_bin,
        }
        argv = self._build_command(mode, context)
        cwd = Path(_render_template(str(self.profile.get("cwd", self.workspace_root)), context)).expanduser()
        env_overrides = {
            key: _render_template(str(value), context)
            for key, value in self.profile.get("env", {}).items()
        }
        env = os.environ.copy()
        env.update(env_overrides)
        env.setdefault("OPENCLAW_BIN", resolved_openclaw_bin)
        openclaw_bin_path = Path(resolved_openclaw_bin).expanduser()
        if openclaw_bin_path.is_absolute():
            bin_dir = str(openclaw_bin_path.parent)
            current_path = env.get("PATH", "")
            path_parts = [part for part in current_path.split(os.pathsep) if part]
            if not path_parts or path_parts[0] != bin_dir:
                env["PATH"] = os.pathsep.join([bin_dir, *path_parts]) if path_parts else bin_dir
        result = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                json.dumps(
                    {
                        "provider": self.provider,
                        "command": argv,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return _load_json_payload(result.stdout, self.provider)

    @staticmethod
    def _normalize_counter_map(raw: Any) -> dict[str, int]:
        if not isinstance(raw, dict):
            return {}
        counters: dict[str, int] = {}
        for key, value in raw.items():
            try:
                counters[str(key)] = int(value)
            except (TypeError, ValueError):
                continue
        return counters

    def _normalize_recent_entry(self, item: Any, index: int) -> dict[str, Any]:
        if not isinstance(item, dict):
            return {
                "id": f"{self.provider}:recent:{index}",
                "text": str(item),
                "scope": None,
                "category": None,
                "importance": None,
                "timestamp": None,
                "metadata": {},
            }

        metadata = item.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                pass
        if metadata is None:
            metadata = {}

        return {
            "id": item.get("id") or f"{self.provider}:recent:{index}",
            "text": item.get("text") or "",
            "scope": item.get("scope"),
            "category": item.get("category"),
            "importance": item.get("importance"),
            "timestamp": item.get("timestamp"),
            "metadata": metadata,
        }

    def _normalize_hit(self, item: Any, index: int) -> dict:
        if not isinstance(item, dict):
            raise ValueError(f"Unexpected hit payload from {self.provider}: {item!r}")
        if "entry" not in item:
            hit = dict(item)
            hit.setdefault("source", "vector")
            hit.setdefault("score", 0.0)
            record = hit.get("record", {})
            if not isinstance(record, dict):
                record = {"value": record}
            record.setdefault("provider", self.provider)
            hit["record"] = record
            hit.setdefault("id", f"{self.provider}:{index}")
            return hit

        entry = item.get("entry") or {}
        if not isinstance(entry, dict):
            raise ValueError(f"Unexpected entry payload from {self.provider}: {entry!r}")
        return {
            "source": "vector",
            "id": entry.get("id") or f"{self.provider}:{index}",
            "record": {
                "provider": self.provider,
                "scope": entry.get("scope"),
                "category": entry.get("category"),
                "text": entry.get("text"),
                "timestamp": entry.get("timestamp"),
                "metadata": entry.get("metadata", {}),
                "sources": item.get("sources", {}),
            },
            "score": float(item.get("score", 0.0) or 0.0),
        }


register_semantic_memory_adapter("memory-lancedb-pro", MemoryLanceDBProAdapter)
