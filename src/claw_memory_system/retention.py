from __future__ import annotations

from dataclasses import dataclass


IMPORTANCE_LEVELS = ("critical", "high", "medium", "low")
RETENTION_POLICIES = (
    "permanent",
    "review",
    "ttl",
    "archive_when_inactive",
    "delete_when_superseded",
)
LIFECYCLE_STATUSES = ("active", "archived", "expired", "superseded", "deleted")


@dataclass(frozen=True)
class RetentionDecision:
    importance: str
    policy: str
    status: str
    score: float


def normalize_importance(value: str, default: str = "medium") -> str:
    return value if value in IMPORTANCE_LEVELS else default


def normalize_policy(value: str, default: str = "review") -> str:
    return value if value in RETENTION_POLICIES else default


def normalize_status(value: str, default: str = "active") -> str:
    return value if value in LIFECYCLE_STATUSES else default


def importance_score(value: str) -> float:
    scores = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
    }
    return scores.get(normalize_importance(value), 0.5)


def recommend_retention(importance: str, *, has_graph_links: bool = False, recently_verified: bool = False) -> RetentionDecision:
    importance = normalize_importance(importance)
    score = importance_score(importance)
    if has_graph_links:
        score += 0.1
    if recently_verified:
        score += 0.1
    if score >= 0.9:
        return RetentionDecision(importance, "permanent", "active", min(score, 1.0))
    if score >= 0.6:
        return RetentionDecision(importance, "review", "active", min(score, 1.0))
    if score >= 0.35:
        return RetentionDecision(importance, "archive_when_inactive", "active", min(score, 1.0))
    return RetentionDecision(importance, "ttl", "active", min(score, 1.0))
