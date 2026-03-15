from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import stat
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.memos_local_migration import (
    build_scope_payloads,
    export_scope_payloads,
    load_chunk_rows,
    row_to_memory,
)


def create_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            create table chunks (
                id text primary key,
                session_key text not null,
                turn_id text not null,
                seq integer not null,
                role text not null,
                content text not null,
                kind text not null default 'paragraph',
                summary text not null default '',
                created_at integer not null,
                updated_at integer not null,
                task_id text,
                content_hash text,
                skill_id text,
                merge_count integer not null default 0,
                last_hit_at integer,
                merge_history text not null default '[]',
                dedup_status text not null default 'active',
                dedup_target text,
                dedup_reason text,
                owner text not null default 'agent:main'
            )
            """
        )
        rows = [
            (
                "active-1",
                "agent:main:main",
                "turn-1",
                0,
                "user",
                "请先部署管理系统查看数据",
                "paragraph",
                "部署管理系统查看数据",
                1000,
                1000,
                None,
                None,
                None,
                0,
                None,
                "[]",
                "active",
                None,
                None,
                "agent:main",
            ),
            (
                "merged-1",
                "agent:main:main",
                "turn-2",
                0,
                "assistant",
                "这是被合并进别的记忆的旧记录",
                "paragraph",
                "旧记录",
                1001,
                1001,
                None,
                None,
                None,
                1,
                None,
                "[]",
                "merged",
                "active-1",
                "新记忆补充细节",
                "agent:main",
            ),
            (
                "duplicate-1",
                "public",
                "turn-3",
                0,
                "assistant",
                "重复记忆",
                "paragraph",
                "重复记忆",
                1002,
                1002,
                None,
                None,
                None,
                0,
                None,
                "[]",
                "duplicate",
                "active-1",
                "与已有记忆意图相同",
                "public",
            ),
            (
                "active-public",
                "public",
                "turn-4",
                1,
                "assistant",
                "公开范围的历史摘要",
                "paragraph",
                "公开范围摘要",
                1003,
                1003,
                "task-1",
                None,
                "skill-1",
                0,
                None,
                "[]",
                "active",
                None,
                None,
                "public",
            ),
        ]
        conn.executemany(
            """
            insert into chunks (
                id, session_key, turn_id, seq, role, content, kind, summary,
                created_at, updated_at, task_id, content_hash, skill_id,
                merge_count, last_hit_at, merge_history, dedup_status,
                dedup_target, dedup_reason, owner
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def write_fake_openclaw(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env python3
import sys

args = sys.argv[1:]
if len(args) >= 3 and args[:2] == ["memory-pro", "import"] and "--dry-run" in args:
    print("DRY RUN - No memories will be imported")
    print(f"Would import 1 memories from {args[2]}")
    raise SystemExit(0)
if len(args) >= 3 and args[:2] == ["memory-pro", "import"]:
    print(f"Import completed: 1 imported, 0 skipped from {args[2]}")
    raise SystemExit(0)

print("unsupported command", args, file=sys.stderr)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class MemosLocalMigrationTest(unittest.TestCase):
    def test_load_chunk_rows_defaults_to_active_only(self) -> None:
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            create_db(db)

            rows = load_chunk_rows(db)

        self.assertEqual([row["id"] for row in rows], ["active-public", "active-1"])

    def test_build_scope_payloads_maps_public_to_global_and_preserves_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            create_db(db)

            payloads = build_scope_payloads(load_chunk_rows(db), source_db=db)

        self.assertEqual(sorted(payloads), ["agent:main", "global"])
        agent_memory = payloads["agent:main"]["memories"][0]
        global_memory = payloads["global"]["memories"][0]
        self.assertEqual(agent_memory["id"], "memos-local:chunk:active-1")
        self.assertEqual(global_memory["id"], "memos-local:chunk:active-public")
        self.assertEqual(agent_memory["text"], "部署管理系统查看数据")
        self.assertEqual(global_memory["text"], "公开范围摘要")
        metadata = global_memory["metadata"]
        self.assertEqual(metadata["legacy"]["owner"], "public")
        self.assertEqual(metadata["legacy"]["task_id"], "task-1")
        self.assertEqual(metadata["legacy"]["content"], "公开范围的历史摘要")
        self.assertEqual(metadata["source"]["table"], "chunks")
        self.assertEqual(global_memory["category"], "other")

    def test_row_to_memory_falls_back_to_content_when_summary_is_single_character(self) -> None:
        row = {
            "id": "active-short-summary",
            "session_key": "agent:main:main",
            "turn_id": "turn-5",
            "seq": 0,
            "role": "assistant",
            "content": "在，我在。请直接重发今天早报，并补一版完整晚间摘要。",
            "kind": "paragraph",
            "summary": "3",
            "created_at": 1004,
            "updated_at": 1004,
            "task_id": None,
            "skill_id": None,
            "merge_count": 0,
            "last_hit_at": None,
            "merge_history": "[]",
            "dedup_status": "active",
            "dedup_target": None,
            "dedup_reason": None,
            "owner": "agent:main",
        }

        memory = row_to_memory(row, source_db=Path("/tmp/memos.db"))

        self.assertEqual(memory["text"], row["content"])
        self.assertEqual(memory["metadata"]["legacy"]["summary"], "3")

    def test_export_scope_payloads_writes_one_file_per_scope(self) -> None:
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            out = Path(tmp) / "out"
            create_db(db)

            written = export_scope_payloads(build_scope_payloads(load_chunk_rows(db), source_db=db), out)

            self.assertEqual(sorted(written), ["agent:main", "global"])
            self.assertTrue((out / "memory-import-agent_main.json").exists())
            self.assertTrue((out / "memory-import-global.json").exists())

    def test_preview_script_runs_dry_run_import_per_scope(self) -> None:
        script = ROOT / "scripts" / "run_memos_local_migration_preview.py"
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            out = Path(tmp) / "out"
            fake_openclaw = Path(tmp) / "openclaw"
            create_db(db)
            write_fake_openclaw(fake_openclaw)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--db",
                    str(db),
                    "--out-dir",
                    str(out),
                    "--openclaw-bin",
                    str(fake_openclaw),
                    "--workspace",
                    str(ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source"]["canonical_chunk_count"], 2)
        self.assertEqual(sorted(payload["payloads"]), ["agent:main", "global"])
        self.assertTrue(payload["dry_run"]["enabled"])
        self.assertTrue(payload["dry_run"]["results"]["agent:main"]["ok"])
        self.assertTrue(payload["dry_run"]["results"]["global"]["ok"])

    def test_import_script_requires_execute_flag(self) -> None:
        script = ROOT / "scripts" / "run_memos_local_import.py"
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            out = Path(tmp) / "out"
            fake_openclaw = Path(tmp) / "openclaw"
            create_db(db)
            write_fake_openclaw(fake_openclaw)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--db",
                    str(db),
                    "--out-dir",
                    str(out),
                    "--openclaw-bin",
                    str(fake_openclaw),
                    "--workspace",
                    str(ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--execute", result.stderr)

    def test_import_script_runs_actual_import_per_scope(self) -> None:
        script = ROOT / "scripts" / "run_memos_local_import.py"
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "memos.db"
            out = Path(tmp) / "out"
            fake_openclaw = Path(tmp) / "openclaw"
            create_db(db)
            write_fake_openclaw(fake_openclaw)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--db",
                    str(db),
                    "--out-dir",
                    str(out),
                    "--openclaw-bin",
                    str(fake_openclaw),
                    "--workspace",
                    str(ROOT),
                    "--execute",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["import"]["enabled"])
        self.assertEqual(sorted(payload["import"]["results"]), ["agent:main", "global"])
        self.assertEqual(payload["import"]["results"]["agent:main"]["imported"], 1)
        self.assertEqual(payload["import"]["results"]["agent:main"]["skipped"], 0)
        self.assertTrue(payload["import"]["results"]["global"]["ok"])


if __name__ == "__main__":
    unittest.main()
