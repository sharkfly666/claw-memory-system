from __future__ import annotations

from pathlib import Path
import json


def write_json_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def write_regression_report(report: dict, reports_dir: Path, *, name: str) -> Path:
    path = reports_dir / f"{name}.json"
    write_json_report(report, path)
    return path
