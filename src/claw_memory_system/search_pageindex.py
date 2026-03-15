from __future__ import annotations

import argparse
from pathlib import Path

from .pageindex import search_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Search SQLite FTS page index")
    parser.add_argument("--db", required=True, help="SQLite DB path")
    parser.add_argument("query", help="FTS query")
    args = parser.parse_args()

    for row in search_index(Path(args.db), args.query):
        record = row["record"]
        print(f"- {row['id']} ({record['source_type']})")
        print(f"  title: {record['title']}")
        print(f"  path:  {record['source_path']}")
        print(f"  when:  {record['updated_at']}")
        print(f"  hit:   {record['snippet']}")


if __name__ == "__main__":
    main()
