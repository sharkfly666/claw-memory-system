from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re

from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .preferences_store import PreferencesStore
from .reports import write_json_report
from .tasks_store import TasksStore


_WORD_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "then", "have", "uses", "using",
    "用户", "要求", "以后", "不要", "当前", "已", "及", "与", "和", "按", "到", "在", "或", "是",
    "一个", "相关", "进行", "当前", "后续", "优先", "memory", "openclaw", "system",
}


@dataclass
class MemoryGovernance:
    workspace_root: Path
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "MemoryGovernance":
        root = workspace_root / "memory-system"
        return cls(
            workspace_root=workspace_root,
            facts=FactsStore(root / "facts" / "facts.json", root / "facts" / "facts.history.jsonl"),
            preferences=PreferencesStore(root / "stores" / "v2" / "preferences.json"),
            tasks=TasksStore(root / "stores" / "v2" / "tasks.json"),
            episodes=EpisodesStore(root / "stores" / "v2" / "episodes.json"),
        )

    def build_report(self) -> dict[str, Any]:
        facts = self.facts.list_facts()
        preferences = self.preferences.list()
        tasks = self.tasks.list()
        episodes = self.episodes.list()

        structured_counts = {
            "facts": len(facts),
            "preferences": len(preferences),
            "tasks": len(tasks),
            "episodes": len(episodes),
        }
        empty_layers = [name for name, count in structured_counts.items() if count == 0]

        stale_active_tasks = []
        for task_id, record in tasks.items():
            state = str(record.get("state", "active"))
            if state == "active" and not str(record.get("last_active_at", "")).strip():
                stale_active_tasks.append({
                    "task_id": task_id,
                    "reason": "active_without_last_active_at",
                    "title": record.get("title") or task_id,
                })

        low_quality_records = []
        for layer_name, items in [
            ("preferences", preferences),
            ("tasks", tasks),
            ("episodes", episodes),
        ]:
            for record_id, record in items.items():
                missing = []
                if not str(record.get("summary", "")).strip():
                    missing.append("summary")
                aliases = record.get("aliases")
                if not isinstance(aliases, list) or not aliases:
                    missing.append("aliases")
                tags = record.get("tags")
                if not isinstance(tags, list) or not tags:
                    missing.append("tags")
                if missing:
                    low_quality_records.append({
                        "layer": layer_name,
                        "id": record_id,
                        "missing": missing,
                    })

        conflicts = self._detect_conflicts(facts, preferences)
        migration_candidates = self._build_migration_candidates(facts, preferences, tasks, episodes)

        report = {
            "schema_version": "memory-governance-report.v1",
            "workspace_root": str(self.workspace_root),
            "structured_counts": structured_counts,
            "empty_layers": empty_layers,
            "issues": {
                "conflicts": conflicts,
                "stale_active_tasks": stale_active_tasks,
                "low_quality_records": low_quality_records,
            },
            "migration_candidates": migration_candidates,
            "summary": {
                "conflict_count": len(conflicts),
                "stale_active_task_count": len(stale_active_tasks),
                "low_quality_record_count": len(low_quality_records),
                "migration_candidate_count": len(migration_candidates),
            },
        }
        return report

    def write_report(self, path: Path | None = None) -> Path:
        out = path or (self.workspace_root / "memory-system" / "reports" / "memory-governance-report.json")
        write_json_report(self.build_report(), out)
        return out

    def _detect_conflicts(self, facts: dict[str, dict], preferences: dict[str, dict]) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        pref_groups = self._group_by_stem(preferences)
        for stem, ids in pref_groups.items():
            active = [pref_id for pref_id in ids if str(preferences[pref_id].get("status", "active")) == "active"]
            if len(active) > 1:
                conflicts.append({
                    "type": "multiple_active_preferences",
                    "stem": stem,
                    "record_ids": active,
                })

        fact_keys = set(facts.keys())
        for pref_id, record in preferences.items():
            tags = [str(x).lower() for x in record.get("tags", [])] if isinstance(record.get("tags"), list) else []
            if "config" in tags or "path" in tags:
                stem = self._key_stem(pref_id)
                related_facts = [key for key in fact_keys if self._key_stem(key) == stem]
                if related_facts:
                    conflicts.append({
                        "type": "preference_fact_overlap",
                        "stem": stem,
                        "preference_id": pref_id,
                        "fact_keys": related_facts,
                    })
        return conflicts

    def _build_migration_candidates(
        self,
        facts: dict[str, dict],
        preferences: dict[str, dict],
        tasks: dict[str, dict],
        episodes: dict[str, dict],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        md_sources = [self.workspace_root / "MEMORY.md"]
        memory_dir = self.workspace_root / "memory"
        if memory_dir.exists():
            md_sources.extend(sorted(memory_dir.glob("*.md")))

        for path in md_sources:
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            snippet = text[:6000]
            lower = snippet.lower()
            if ("偏好" in snippet or "喜欢" in snippet or "直接高效" in snippet or "少废话" in snippet) and not preferences:
                candidates.append({
                    "source": str(path),
                    "suggested_layer": "preferences",
                    "reason": "found preference-like language in markdown while preferences layer is empty",
                    "suggested_id": "user.communication_style",
                })
            if ("todo" in lower or "待办" in snippet or "优化" in snippet or "修复" in snippet) and not tasks:
                candidates.append({
                    "source": str(path),
                    "suggested_layer": "tasks",
                    "reason": "found task-like language in markdown while tasks layer is empty",
                    "suggested_id": "task.bootstrap-from-markdown",
                })
            if ("问题" in snippet or "修复" in snippet or "关闭" in snippet or "切换" in snippet) and not episodes:
                candidates.append({
                    "source": str(path),
                    "suggested_layer": "episodes",
                    "reason": "found event/decision-like language in markdown while episodes layer is empty",
                    "suggested_id": f"episode.{path.stem}",
                })

        for key, record in facts.items():
            tokens = self._tokens_from_record(key, record)
            if any(tok in {"prefer", "preference", "偏好", "喜欢", "少废话", "style", "communication"} for tok in tokens):
                candidates.append({
                    "source": f"fact:{key}",
                    "suggested_layer": "preferences",
                    "reason": "fact record looks preference-like and may belong in preferences",
                    "suggested_id": self._normalize_id(key),
                })
            if any(tok in {"fix", "修复", "优化", "问题", "timeout", "阻塞"} for tok in tokens):
                candidates.append({
                    "source": f"fact:{key}",
                    "suggested_layer": "episodes",
                    "reason": "fact record contains incident/process wording and may need an episode companion",
                    "suggested_id": f"episode.{self._normalize_id(key)}",
                })
        return self._dedupe_candidates(candidates)

    def _group_by_stem(self, items: dict[str, dict]) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for key in items.keys():
            stem = self._key_stem(key)
            grouped.setdefault(stem, []).append(key)
        return grouped

    def _key_stem(self, key: str) -> str:
        text = str(key).strip().lower()
        if "." in text:
            parts = [part for part in text.split(".") if part]
            if len(parts) >= 2:
                owner = parts[0]
                domain_tokens = [token for token in re.split(r"[_-]", ".".join(parts[1:])) if token]
                if domain_tokens:
                    domain = domain_tokens[0]
                    if domain in {"communication", "storage", "github", "pansou", "memory", "daily", "briefing"}:
                        return f"{owner}.{domain}"
                return ".".join(parts[:2])
        if "_" in text:
            return "_".join(text.split("_")[:2])
        return text

    def _tokens_from_record(self, key: str, record: dict[str, Any]) -> set[str]:
        hay = " ".join([
            str(key),
            str(record.get("summary", "")),
            str(record.get("notes", "")),
            str(record.get("value", "")),
            " ".join(str(x) for x in record.get("aliases", []) if isinstance(record.get("aliases"), list)),
            " ".join(str(x) for x in record.get("tags", []) if isinstance(record.get("tags"), list)),
        ])
        tokens = {m.group(0).lower() for m in _WORD_RE.finditer(hay)}
        return {tok for tok in tokens if tok not in _STOPWORDS and len(tok) > 1}

    def _normalize_id(self, value: str) -> str:
        text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", str(value).strip().lower())
        text = re.sub(r"-+", "-", text).strip("-._")
        return text or "candidate"

    def _dedupe_candidates(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        deduped = []
        for item in items:
            key = (item.get("source", ""), item.get("suggested_layer", ""), item.get("suggested_id", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped


def build_memory_governance_report(workspace_root: Path) -> dict[str, Any]:
    return MemoryGovernance.from_workspace(workspace_root).build_report()


def write_memory_governance_report(workspace_root: Path, path: Path | None = None) -> Path:
    return MemoryGovernance.from_workspace(workspace_root).write_report(path)
