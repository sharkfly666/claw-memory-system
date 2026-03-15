from __future__ import annotations

from pathlib import Path
import argparse
import json

from .batch_governance import run_batch_governance, write_batch_governance_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run claw-memory-system batch governance workflow.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--write", action="store_true", help="Write the batch governance report to the default reports path.")
    parser.add_argument("--no-auto-apply-safe", action="store_true")
    parser.add_argument("--no-refresh-graph", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    auto_apply_safe = not args.no_auto_apply_safe
    refresh_graph = not args.no_refresh_graph

    if args.write:
        path = write_batch_governance_report(
            workspace,
            auto_apply_safe=auto_apply_safe,
            refresh_graph=refresh_graph,
        )
        payload = {
            "ok": True,
            "path": str(path),
            "report": json.loads(path.read_text(encoding="utf-8")),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    payload = run_batch_governance(
        workspace,
        auto_apply_safe=auto_apply_safe,
        refresh_graph=refresh_graph,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
