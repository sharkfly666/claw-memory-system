from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .search_router import SearchRouter


@dataclass
class EvaluationCase:
    case_id: str
    query: str
    expected_sources: list[str]
    description: str = ""


def load_cases(path: Path) -> list[EvaluationCase]:
    raw = json.loads(path.read_text())
    cases: list[EvaluationCase] = []
    for item in raw:
        cases.append(
            EvaluationCase(
                case_id=item["case_id"],
                query=item["query"],
                expected_sources=item.get("expected_sources", []),
                description=item.get("description", ""),
            )
        )
    return cases


def evaluate_cases(router: SearchRouter, cases: list[EvaluationCase]) -> dict:
    results = []
    passed = 0
    for case in cases:
        route_result = router.search(case.query)
        sources = [hit["source"] for hit in route_result.hits]
        matched = any(source in sources for source in case.expected_sources) if case.expected_sources else bool(route_result.hits)
        if matched:
            passed += 1
        results.append(
            {
                "case_id": case.case_id,
                "query": case.query,
                "route": route_result.route,
                "expected_sources": case.expected_sources,
                "actual_sources": sources,
                "matched": matched,
                "hit_count": len(route_result.hits),
            }
        )
    return {
        "total": len(cases),
        "passed": passed,
        "pass_rate": (passed / len(cases)) if cases else 0.0,
        "results": results,
    }


def write_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
