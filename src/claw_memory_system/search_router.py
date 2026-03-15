from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .graph_store import GraphStore
from .preferences_store import PreferencesStore
from .session_store import SessionStore
from .tasks_store import TasksStore
from .retention import importance_score


QueryFn = Callable[[str], list[dict]]


@dataclass
class SearchRouteResult:
    query: str
    route: str
    hits: list[dict] = field(default_factory=list)


@dataclass
class SearchRouter:
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore
    sessions: SessionStore
    graph: GraphStore | None = None
    vector_query: QueryFn | None = None
    exact_query: QueryFn | None = None

    def classify(self, query: str) -> str:
        q = query.lower()
        preference_tokens = [
            "偏好", "风格", "喜欢", "怎么回答", "少废话", "direct", "communication",
            "proactive", "autonomous", "technical", "architecture judgment",
        ]
        session_tokens = ["当前", "现在在做", "刚才", "next", "下一步", "进行中", "session", "active"]
        task_tokens = ["任务", "问题", "评估", "处理到哪", "阻塞", "状态", "task", "validation", "fix"]
        fact_tokens = ["配置", "路径", "目录", "key", "id", "地址", "workspace", "minscore", "8:00", "pansou"]
        skill_tokens = ["技能", "skill", "经验", "方法"]
        if any(token in q for token in preference_tokens):
            return "preference"
        if any(token in q for token in session_tokens):
            return "session"
        if any(token in q for token in task_tokens):
            return "task"
        if any(token in q for token in fact_tokens):
            return "fact"
        if any(token in q for token in skill_tokens):
            return "skill"
        return "history"

    def search(self, query: str) -> SearchRouteResult:
        route = self.classify(query)
        if route == "preference":
            return SearchRouteResult(query, route, self._search_preferences(query) + self._query_optional(self.exact_query, query))
        if route == "session":
            hits = self._search_sessions(query) + self._search_tasks(query)
            return SearchRouteResult(query, route, self._merge_with_graph(hits))
        if route == "task":
            hits = self._search_tasks(query) + self._search_sessions(query) + self._search_episodes(query)
            return SearchRouteResult(query, route, self._merge_with_graph(hits))
        if route == "fact":
            hits = self._search_facts(query) + self._search_episodes(query) + self._query_optional(self.exact_query, query)
            return SearchRouteResult(query, route, self._merge_with_graph(hits))
        if route == "skill":
            graph_hits = self._search_graph(query) if self.graph else []
            return SearchRouteResult(query, route, self._merge_with_graph(graph_hits + self._search_episodes(query)))
        hits = self._search_episodes(query) + self._query_optional(self.vector_query, query) + self._query_optional(self.exact_query, query)
        return SearchRouteResult(query, route, self._merge_with_graph(hits))

    def _query_optional(self, fn: QueryFn | None, query: str) -> list[dict]:
        if not fn:
            return []
        return fn(query)

    def _contains(self, value: object, query: str) -> bool:
        q = query.lower()
        if isinstance(value, dict):
            alias_tokens = [str(x).lower() for x in value.get("aliases", [])] if isinstance(value.get("aliases"), list) else []
            tag_tokens = [str(x).lower() for x in value.get("tags", [])] if isinstance(value.get("tags"), list) else []
            if any(q in token or token in q for token in alias_tokens + tag_tokens):
                return True
        hay = str(value).lower()
        if q in hay:
            return True
        tokens = [t for t in q.replace("?", " ").replace("？", " ").split() if t]
        if not tokens:
            tokens = [q]
        matched = sum(1 for token in tokens if token in hay)
        return matched >= max(1, len(tokens) // 2)

    def _search_map(self, items: dict[str, dict], query: str, source: str) -> list[dict]:
        hits: list[dict] = []
        for key, item in items.items():
            if self._contains(item, query):
                hits.append({
                    "source": source,
                    "id": key,
                    "record": item,
                    "score": self._score_record(item, source),
                })
        hits.sort(key=lambda x: x.get("score", 0), reverse=True)
        return hits

    def _score_record(self, record: dict, source: str) -> float:
        importance = str(record.get("importance", "medium")) if isinstance(record, dict) else "medium"
        status = str(record.get("status", "active")) if isinstance(record, dict) else "active"
        base = importance_score(importance)
        source_bonus = {
            "preferences": 0.25,
            "sessions": 0.22,
            "tasks": 0.2,
            "facts": 0.18,
            "episodes": 0.12,
            "graph": 0.08,
        }.get(source, 0.0)
        status_penalty = {
            "active": 0.0,
            "archived": -0.2,
            "superseded": -0.35,
            "expired": -0.4,
            "deleted": -1.0,
        }.get(status, 0.0)
        return max(0.0, base + source_bonus + status_penalty)

    def _search_facts(self, query: str) -> list[dict]:
        return self._search_map(self.facts.list_facts(), query, "facts")

    def _search_preferences(self, query: str) -> list[dict]:
        return self._search_map(self.preferences.list(), query, "preferences")

    def _search_tasks(self, query: str) -> list[dict]:
        return self._search_map(self.tasks.list(), query, "tasks")

    def _search_episodes(self, query: str) -> list[dict]:
        return self._search_map(self.episodes.list(), query, "episodes")

    def _search_sessions(self, query: str) -> list[dict]:
        return self._search_map(self.sessions.list(), query, "sessions")

    def _search_graph(self, query: str) -> list[dict]:
        if not self.graph:
            return []
        hits = []
        for node_id, node in self.graph.list_nodes().items():
            if self._contains(node, query):
                hits.append({"source": "graph", "id": node_id, "record": node})
        return hits

    def _merge_with_graph(self, hits: list[dict]) -> list[dict]:
        if not self.graph or not hits:
            return hits
        merged = list(hits)
        seen = {(hit.get("source"), hit.get("id")) for hit in hits}
        related_ids = {hit.get("id") for hit in hits if hit.get("id")}
        for edge in self.graph.list_edges():
            source = edge.get("source")
            target = edge.get("target")
            if source in related_ids and ("graph", target) not in seen:
                node = self.graph.get_node(target)
                if node:
                    merged.append({
                        "source": "graph.expanded",
                        "id": target,
                        "record": node,
                        "via": {"source": source, "relation": edge.get("relation")},
                        "score": self._score_record(node, "graph") - 0.05,
                    })
                    seen.add(("graph", target))
            if target in related_ids and ("graph", source) not in seen:
                node = self.graph.get_node(source)
                if node:
                    merged.append({
                        "source": "graph.expanded",
                        "id": source,
                        "record": node,
                        "via": {"source": target, "relation": edge.get("relation")},
                        "score": self._score_record(node, "graph") - 0.05,
                    })
                    seen.add(("graph", source))
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        return merged
