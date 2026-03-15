from __future__ import annotations

from pathlib import Path
import json
import re
import sqlite3
import subprocess


DEFAULT_STATUSES = ("active",)
_DRY_RUN_RE = re.compile(r"Would import\s+(?P<count>\d+)\s+memories")
_IMPORT_RE = re.compile(r"Import completed:\s+(?P<imported>\d+)\s+imported,\s+(?P<skipped>\d+)\s+skipped")


def load_chunk_rows(
    db_path: Path,
    *,
    statuses: tuple[str, ...] = DEFAULT_STATUSES,
    owner: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    clauses = []
    params: list[object] = []
    if statuses:
        placeholders = ",".join("?" for _ in statuses)
        clauses.append(f"dedup_status in ({placeholders})")
        params.extend(statuses)
    if owner:
        clauses.append("owner = ?")
        params.append(owner)
    where = f"where {' and '.join(clauses)}" if clauses else ""
    limit_sql = " limit ?" if limit is not None else ""
    if limit is not None:
        params.append(limit)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            select
              id, session_key, turn_id, seq, role, content, kind, summary,
              created_at, updated_at, task_id, skill_id, merge_count,
              last_hit_at, merge_history, dedup_status, dedup_target,
              dedup_reason, owner
            from chunks
            {where}
            order by created_at desc
            {limit_sql}
            """,
            params,
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def map_owner_to_scope(owner: str | None, default_scope: str = "global") -> str:
    value = (owner or "").strip()
    if not value or value == "public":
        return default_scope
    return value


def sanitize_filename_scope(scope: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", scope)


def _importance_for_row(row: dict) -> float:
    if row.get("role") == "user":
        return 0.78
    if row.get("summary"):
        return 0.68
    return 0.62


def _text_for_row(summary: str, content: str) -> str:
    if summary and len(summary) > 1:
        return summary
    return content or summary


def row_to_memory(row: dict, *, source_db: Path, default_scope: str = "global") -> dict:
    summary = str(row.get("summary") or "").strip()
    content = str(row.get("content") or "").strip()
    text = _text_for_row(summary, content)
    metadata = {
        "source": {
            "plugin": "memos-local-openclaw-plugin",
            "db": str(source_db),
            "table": "chunks",
        },
        "legacy": {
            "id": row["id"],
            "session_key": row["session_key"],
            "turn_id": row["turn_id"],
            "seq": row["seq"],
            "role": row["role"],
            "kind": row["kind"],
            "summary": summary,
            "content": content,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "task_id": row["task_id"],
            "skill_id": row["skill_id"],
            "merge_count": row["merge_count"],
            "last_hit_at": row["last_hit_at"],
            "merge_history": row["merge_history"],
            "dedup_status": row["dedup_status"],
            "dedup_target": row["dedup_target"],
            "dedup_reason": row["dedup_reason"],
            "owner": row["owner"],
        },
    }
    return {
        "id": f"memos-local:chunk:{row['id']}",
        "text": text,
        "category": "other",
        "importance": _importance_for_row(row),
        "timestamp": int(row["created_at"]),
        "metadata": metadata,
        "scope": map_owner_to_scope(row.get("owner"), default_scope=default_scope),
    }


def build_scope_payloads(
    rows: list[dict],
    *,
    source_db: Path,
    default_scope: str = "global",
) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        memory = row_to_memory(row, source_db=source_db, default_scope=default_scope)
        scope = memory.pop("scope")
        grouped.setdefault(scope, []).append(memory)
    return {scope: {"memories": memories} for scope, memories in grouped.items()}


def export_scope_payloads(payloads: dict[str, dict], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for scope, payload in payloads.items():
        name = f"memory-import-{sanitize_filename_scope(scope)}.json"
        path = out_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written[scope] = str(path)
    return written


def run_command(cmd: list[str], *, cwd: Path) -> dict:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }


def summarize_import_result(result: dict, *, dry_run: bool) -> dict:
    summary = dict(result)
    summary["mode"] = "dry-run" if dry_run else "import"
    summary["planned"] = None
    summary["imported"] = None
    summary["skipped"] = None
    pattern = _DRY_RUN_RE if dry_run else _IMPORT_RE
    match = pattern.search(str(result.get("stdout") or ""))
    if not match:
        return summary
    if dry_run:
        summary["planned"] = int(match.group("count"))
        return summary
    summary["imported"] = int(match.group("imported"))
    summary["skipped"] = int(match.group("skipped"))
    return summary


def run_memory_pro_imports(
    written: dict[str, str],
    *,
    workspace: Path,
    openclaw_bin: str,
    dry_run: bool,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for scope, file_path in written.items():
        cmd = [openclaw_bin, "memory-pro", "import", file_path, "--scope", scope]
        if dry_run:
            cmd.append("--dry-run")
        raw = run_command(cmd, cwd=workspace)
        results[scope] = summarize_import_result(raw, dry_run=dry_run)
    return results
