from __future__ import annotations

from typing import Any
import hashlib
import re


def normalize_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return text


def dedupe_key_for_candidate(candidate: dict[str, Any]) -> str:
    layer = str(candidate.get("target_layer", "")).strip().lower()
    summary = normalize_text(str(candidate.get("summary", "")))
    user_text = normalize_text(str(candidate.get("user_text", "")))
    reason = normalize_text(str(candidate.get("reason", "")))
    basis = "|".join([layer, summary, user_text, reason])
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()
