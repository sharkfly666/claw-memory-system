from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    facts: Path
    memory_md: Path
    memory_dir: Path

    @classmethod
    def from_root(cls, root: str | Path, facts: str | Path | None = None) -> "WorkspacePaths":
        root = Path(root).resolve()
        return cls(
            root=root,
            facts=Path(facts).resolve() if facts else root / "memory-system" / "facts" / "facts.json",
            memory_md=root / "MEMORY.md",
            memory_dir=root / "memory",
        )
