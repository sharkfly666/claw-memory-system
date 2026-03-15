from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .search_router import SearchRouter


@dataclass
class RetrievalInspector:
    router: SearchRouter

    def inspect(self, query: str) -> dict[str, Any]:
        route = self.router.classify(query)
        by_layer = {
            "preferences": self.router._search_preferences(query),
            "sessions": self.router._search_sessions(query),
            "tasks": self.router._search_tasks(query),
            "facts": self.router._search_facts(query),
            "episodes": self.router._search_episodes(query),
            "graph": self.router._search_graph(query) if self.router.graph else [],
        }
        if self.router.exact_query:
            by_layer["exact"] = self.router.exact_query(query)
        if self.router.vector_query:
            by_layer["vector"] = self.router.vector_query(query)
        final_result = self.router.search(query)
        graph_expanded = [hit for hit in final_result.hits if hit.get("source") == "graph.expanded"]
        return {
            "query": query,
            "route": route,
            "layer_hits": {k: len(v) for k, v in by_layer.items()},
            "layer_results": by_layer,
            "graph_expansion_count": len(graph_expanded),
            "graph_expansions": graph_expanded,
            "final_hits": final_result.hits,
        }
