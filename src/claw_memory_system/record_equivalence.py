from __future__ import annotations

from typing import Any
import json


def _normalized(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalized(v) for k, v in sorted(value.items()) if k not in {"updated_at", "last_verified", "created_at"}}
    if isinstance(value, list):
        return sorted((_normalized(v) for v in value), key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
    if isinstance(value, str):
        return value.strip()
    return value


def records_equivalent(existing: dict[str, Any] | None, incoming: dict[str, Any] | None) -> bool:
    if not isinstance(existing, dict) or not isinstance(incoming, dict):
        return False
    return _normalized(existing) == _normalized(incoming)
