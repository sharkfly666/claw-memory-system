from __future__ import annotations

from typing import Any


def ok(data: Any = None, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "meta": meta or {},
        "error": None,
    }


def err(message: str, *, code: str = "error", meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "data": None,
        "meta": meta or {},
        "error": {
            "code": code,
            "message": message,
        },
    }
