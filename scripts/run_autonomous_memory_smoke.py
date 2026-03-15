from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    with TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "workspace"
        bootstrap = run([
            PYTHON,
            "-m",
            "claw_memory_system.bootstrap_openclaw_instance",
            "--workspace",
            str(workspace),
            "--repo",
            str(ROOT),
        ], cwd=ROOT, env=env)
        if not bootstrap["ok"]:
            print(json.dumps({"ok": False, "stage": "bootstrap", **bootstrap}, ensure_ascii=False, indent=2))
            return 1

        classify = run([
            PYTHON,
            "-m",
            "claw_memory_system.turn_candidate_bridge_cli",
            "--workspace",
            str(workspace),
            "--user-text",
            "以后涉及 GitHub 下载优先用 gh，不要 git clone",
        ], cwd=ROOT, env=env)
        if not classify["ok"]:
            print(json.dumps({"ok": False, "stage": "turn-queue", **classify}, ensure_ascii=False, indent=2))
            return 1

        batch = run([
            PYTHON,
            "-m",
            "claw_memory_system.batch_governance_cli",
            "--workspace",
            str(workspace),
            "--write",
        ], cwd=ROOT, env=env)
        if not batch["ok"]:
            print(json.dumps({"ok": False, "stage": "batch-governance", **batch}, ensure_ascii=False, indent=2))
            return 1

        report = json.loads(batch["stdout"])
        summary = report.get("report", {}).get("summary", {})
        output = {
            "ok": True,
            "workspace": str(workspace),
            "summary": summary,
            "report_path": report.get("path"),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
