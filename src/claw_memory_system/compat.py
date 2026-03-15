from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class StoreVersion:
    kind: str
    version: str


SUPPORTED_FACTS_VERSIONS = {"1.0"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def detect_facts_version(path: Path) -> StoreVersion:
    data = read_json(path)
    version = data.get("version")
    if version not in SUPPORTED_FACTS_VERSIONS:
        raise ValueError(f"Unsupported facts version: {version!r}")
    return StoreVersion(kind="facts", version=version)


def ensure_facts_compatible(path: Path) -> None:
    detect_facts_version(path)
