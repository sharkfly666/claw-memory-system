from __future__ import annotations

from pathlib import Path
import json

from .api_response import ok, err


def read_report(report_path: Path) -> dict:
    return json.loads(report_path.read_text())


def latest_report_response(workspace_root: Path, report_name: str = "memory_v2_realish_baseline") -> dict:
    path = workspace_root / "memory-system" / "reports" / f"{report_name}.json"
    if not path.exists():
        return err("Report not found", code="report_not_found", meta={"path": str(path)})
    data = read_report(path)
    return ok(data, meta={"path": str(path), "report_name": report_name})
