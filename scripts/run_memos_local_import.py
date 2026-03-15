from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.memos_local_migration import (
    build_scope_payloads,
    export_scope_payloads,
    load_chunk_rows,
    run_memory_pro_imports,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import canonical memos-local chunks into memory-pro, one scope payload at a time.")
    parser.add_argument("--db", default=str(Path("~/.openclaw/memos-local/memos.db").expanduser()), help="Path to memos-local SQLite database.")
    parser.add_argument("--out-dir", required=True, help="Directory where per-scope memory-pro import payloads will be written.")
    parser.add_argument("--workspace", default=str(Path("~/.openclaw/workspace").expanduser()), help="Workspace path used as cwd for openclaw imports.")
    parser.add_argument("--openclaw-bin", default="openclaw", help="OpenClaw executable to use for imports.")
    parser.add_argument("--owner", help="Optional owner filter, e.g. agent:main.")
    parser.add_argument("--limit", type=int, help="Optional maximum number of canonical chunks to export.")
    parser.add_argument("--statuses", nargs="+", default=["active"], help="Chunk statuses to export. Defaults to active only.")
    parser.add_argument("--execute", action="store_true", help="Actually import into memory-pro. Required for this script to run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.execute:
        print("Refusing to import without --execute. Use run_memos_local_migration_preview.py for dry-run preview.", file=sys.stderr)
        return 2

    db = Path(args.db).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    rows = load_chunk_rows(
        db,
        statuses=tuple(args.statuses),
        owner=args.owner,
        limit=args.limit,
    )
    payloads = build_scope_payloads(rows, source_db=db)
    written = export_scope_payloads(payloads, out_dir)
    import_results = run_memory_pro_imports(
        written,
        workspace=workspace,
        openclaw_bin=args.openclaw_bin,
        dry_run=False,
    )
    summary = {
        "source": {
            "db": str(db),
            "statuses": list(args.statuses),
            "owner": args.owner,
            "canonical_chunk_count": len(rows),
        },
        "payloads": {
            scope: {
                "file": path,
                "count": len(payloads[scope]["memories"]),
            }
            for scope, path in written.items()
        },
        "import": {
            "enabled": True,
            "results": import_results,
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(result.get("ok") for result in import_results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
