from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sqlite3


def chunk_markdown(text: str, chunk_size: int = 1400):
    text = text.strip()
    if not text:
        return []
    lines = text.splitlines()
    chunks = []
    current = []
    current_len = 0
    current_title = ""
    for line in lines:
        if line.startswith("#") and current:
            chunks.append((current_title, "\n".join(current).strip()))
            current = [line]
            current_len = len(line)
            current_title = line.lstrip("# ").strip()
            continue
        if not current:
            current_title = line.lstrip("# ").strip() if line.startswith("#") else ""
        if current_len + len(line) + 1 > chunk_size and current:
            chunks.append((current_title, "\n".join(current).strip()))
            current = [line]
            current_len = len(line)
            if line.startswith("#"):
                current_title = line.lstrip("# ").strip()
            continue
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append((current_title, "\n".join(current).strip()))
    return chunks


def init_db(conn: sqlite3.Connection, schema_sql: str):
    conn.executescript(schema_sql)
    conn.execute("DELETE FROM documents")
    conn.execute("DELETE FROM documents_fts")
    conn.commit()


def insert_doc(conn: sqlite3.Connection, doc: dict):
    conn.execute(
        """
        INSERT OR REPLACE INTO documents
        (doc_id, source_type, source_path, title, entity, key, aliases, tags, text, scope, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc["doc_id"], doc["source_type"], doc.get("source_path"), doc.get("title"),
            doc.get("entity"), doc.get("key"), doc.get("aliases", ""), doc.get("tags", ""),
            doc["text"], doc.get("scope"), doc.get("status", "active"), doc.get("created_at"),
            doc.get("updated_at")
        ),
    )
    conn.execute(
        "INSERT INTO documents_fts (doc_id, title, entity, key, aliases, tags, text) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc["doc_id"], doc.get("title", ""), doc.get("entity", ""), doc.get("key", ""), doc.get("aliases", ""), doc.get("tags", ""), doc["text"]),
    )


def index_facts(conn: sqlite3.Connection, facts_path: Path, root: Path) -> int:
    if not facts_path.exists():
        return 0
    data = json.loads(facts_path.read_text())
    count = 0
    for key, fact in data.get("facts", {}).items():
        value = fact.get("value")
        value_text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        text = f"{key} = {value_text}"
        if fact.get("notes"):
            text += f"\n{fact['notes']}"
        insert_doc(conn, {
            "doc_id": f"fact:{key}",
            "source_type": "fact",
            "source_path": str(facts_path.relative_to(root)),
            "title": key,
            "entity": key,
            "key": key,
            "aliases": " ".join(fact.get("aliases", [])),
            "tags": " ".join(fact.get("tags", [])),
            "text": text,
            "scope": fact.get("scope", "global"),
            "status": fact.get("status", "active"),
            "created_at": fact.get("created_at"),
            "updated_at": fact.get("updated_at"),
        })
        count += 1
    return count


def index_markdown_file(conn: sqlite3.Connection, path: Path, root: Path, source_type: str) -> int:
    if not path.exists():
        return 0
    chunks = chunk_markdown(path.read_text(errors="ignore"))
    count = 0
    for i, (title, chunk) in enumerate(chunks, start=1):
        if not chunk:
            continue
        stat = path.stat()
        insert_doc(conn, {
            "doc_id": f"{source_type}:{path.name}:{i}",
            "source_type": source_type,
            "source_path": str(path.relative_to(root)),
            "title": title or path.stem,
            "entity": path.stem,
            "key": None,
            "aliases": "",
            "tags": source_type,
            "text": chunk,
            "scope": "global",
            "status": "active",
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
        count += 1
    return count


def search_index(db_path: Path, query: str, *, limit: int = 10) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path.resolve())
    conn.row_factory = sqlite3.Row
    try:
        try:
            rows = conn.execute(
                """
                SELECT d.doc_id, d.source_type, d.title, d.source_path, d.updated_at,
                       snippet(documents_fts, 6, '[', ']', ' … ', 18) AS snippet
                FROM documents_fts
                JOIN documents d USING (doc_id)
                WHERE documents_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    finally:
        conn.close()

    return [
        {
            "source": "exact",
            "id": row["doc_id"],
            "record": {
                "title": row["title"],
                "source_type": row["source_type"],
                "source_path": row["source_path"],
                "updated_at": row["updated_at"],
                "snippet": row["snippet"],
            },
            "score": 0.65,
        }
        for row in rows
    ]
