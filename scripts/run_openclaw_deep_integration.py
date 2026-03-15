from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.openclaw_runtime import run_deep_integration


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deep OpenClaw integration and migration checks against a local installation.")
    parser.add_argument("--repo", default=str(ROOT), help="Repository root path. Defaults to the current repo.")
    parser.add_argument("--openclaw-home", default=str(Path("~/.openclaw").expanduser()), help="Path to the local OpenClaw home directory.")
    parser.add_argument("--workspace", help="Optional workspace override. Defaults to the workspace in openclaw.json or <openclaw-home>/workspace.")
    parser.add_argument("--openclaw-bin", default="openclaw", help="OpenClaw executable to use for runtime checks.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when the local runtime is not ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run_deep_integration(
        repo=Path(args.repo).expanduser().resolve(),
        openclaw_home=Path(args.openclaw_home).expanduser().resolve(),
        openclaw_bin=args.openclaw_bin,
        workspace=Path(args.workspace).expanduser().resolve() if args.workspace else None,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.strict and not payload.get("ready"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
