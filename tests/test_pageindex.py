from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.pageindex import index_markdown_file, init_db, search_index


class PageIndexTest(unittest.TestCase):
    def test_search_index_returns_empty_list_for_invalid_fts_query(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory = root / "MEMORY.md"
            memory.write_text("# Primary model\nUse GPT-5.\n")
            db_path = root / "pageindex.sqlite"

            conn = sqlite3.connect(db_path)
            try:
                init_db(conn, (ROOT / "sql" / "pageindex_schema.sql").read_text())
                index_markdown_file(conn, memory, root, "memory_md")
                conn.commit()
            finally:
                conn.close()

            self.assertEqual(search_index(db_path, '"unterminated'), [])


if __name__ == "__main__":
    unittest.main()
