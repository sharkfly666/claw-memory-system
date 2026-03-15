from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from .pageindex import init_db, index_facts, index_markdown_file
from .paths import WorkspacePaths


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SQLite FTS page index")
    parser.add_argument("--root", required=True, help="Workspace root")
    parser.add_argument("--db", required=True, help="SQLite DB output path")
    parser.add_argument("--facts", help="Facts JSON path")
    parser.add_argument("--schema", help="Schema SQL path")
    args = parser.parse_args()

    paths = WorkspacePaths.from_root(args.root, args.facts)
    db_path = Path(args.db).resolve()
    schema_path = Path(args.schema).resolve() if args.schema else Path(__file__).resolve().parents[2] / "sql" / "pageindex_schema.sql"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        init_db(conn, schema_path.read_text())
        total = 0
        total += index_facts(conn, paths.facts, paths.root)
        total += index_markdown_file(conn, paths.memory_md, paths.root, "memory_md")
        if paths.memory_dir.exists():
            for md in sorted(paths.memory_dir.glob("*.md")):
                total += index_markdown_file(conn, md, paths.root, "daily_memory")
        conn.commit()
        print(f"Indexed {total} documents into {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
