from __future__ import annotations

from pathlib import Path
import argparse
import json
import shutil

from .paths import ensure_dir


def _write_facts_cli_wrapper(path: Path, repo: Path) -> None:
    facts_path = path.with_name("facts.json")
    history_path = path.with_name("facts.history.jsonl")
    path.write_text(
        """from pathlib import Path
import sys

REPO = Path({repo!r})
sys.path.insert(0, str(REPO / "src"))

from claw_memory_system.facts_cli import main as _main


def main() -> None:
    argv = sys.argv[1:]
    if "--facts" not in argv:
        argv = ["--facts", {facts_path!r}, "--history", {history_path!r}, *argv]
    sys.argv = [sys.argv[0], *argv]
    _main()


if __name__ == "__main__":
    main()
""".format(
            repo=str(repo.resolve()),
            facts_path=str(facts_path),
            history_path=str(history_path),
        )
    )


def _write_build_pageindex_wrapper(path: Path, repo: Path) -> None:
    workspace_root = path.resolve().parents[2]
    db_path = path.with_name("pageindex.sqlite")
    path.write_text(
        """from pathlib import Path
import sys

REPO = Path({repo!r})
sys.path.insert(0, str(REPO / "src"))

from claw_memory_system.build_pageindex import main as _main


def main() -> None:
    argv = sys.argv[1:]
    if "--root" not in argv:
        argv = ["--root", {workspace_root!r}, "--db", {db_path!r}, *argv]
    sys.argv = [sys.argv[0], *argv]
    _main()


if __name__ == "__main__":
    main()
""".format(
            repo=str(repo.resolve()),
            workspace_root=str(workspace_root),
            db_path=str(db_path),
        )
    )


def _write_search_pageindex_wrapper(path: Path, repo: Path) -> None:
    db_path = path.with_name("pageindex.sqlite")
    path.write_text(
        """from pathlib import Path
import sys

REPO = Path({repo!r})
sys.path.insert(0, str(REPO / "src"))

from claw_memory_system.search_pageindex import main as _main


def main() -> None:
    argv = sys.argv[1:]
    if "--db" not in argv:
        argv = ["--db", {db_path!r}, *argv]
    sys.argv = [sys.argv[0], *argv]
    _main()


if __name__ == "__main__":
    main()
""".format(
            repo=str(repo.resolve()),
            db_path=str(db_path),
        )
    )


def bootstrap(workspace: Path, repo: Path):
    runtime = workspace / "memory-system"
    ensure_dir(runtime)
    ensure_dir(runtime / "facts")
    ensure_dir(runtime / "index")
    ensure_dir(runtime / "schemas")
    ensure_dir(runtime / "stores")
    ensure_dir(runtime / "stores" / "v2")
    ensure_dir(runtime / "reports")
    ensure_dir(runtime / "migrations")

    shutil.copy2(repo / "schemas" / "facts.v1.schema.json", runtime / "schemas" / "facts.v1.schema.json")
    for name in [
        "preferences.v1.schema.json",
        "tasks.v1.schema.json",
        "episodes.v1.schema.json",
        "skills.v1.schema.json",
        "session.v1.schema.json",
        "models.v1.schema.json",
        "graph.v1.schema.json",
        "migration-candidates.v1.schema.json",
        "skill-proposals.v1.schema.json",
    ]:
        src = repo / "schemas" / name
        if src.exists():
            shutil.copy2(src, runtime / "schemas" / name)

    _write_facts_cli_wrapper(runtime / "facts" / "facts_cli.py", repo)
    _write_build_pageindex_wrapper(runtime / "index" / "build_pageindex.py", repo)
    _write_search_pageindex_wrapper(runtime / "index" / "search_pageindex.py", repo)
    shutil.copy2(repo / "src" / "claw_memory_system" / "extract_fact_candidates.py", runtime / "migrations" / "extract_fact_candidates.py") if (repo / "src" / "claw_memory_system" / "extract_fact_candidates.py").exists() else None

    facts_path = runtime / "facts" / "facts.json"
    if not facts_path.exists():
        facts_path.write_text('{\n  "version": "1.0",\n  "facts": {}\n}\n')

    for name, schema_version, root_key in [
        ("preferences.json", "preferences.v1", "preferences"),
        ("tasks.json", "tasks.v1", "tasks"),
        ("episodes.json", "episodes.v1", "episodes"),
        ("skills.json", "skills.v1", "skills"),
        ("session.json", "session.v1", "sessions"),
        ("graph.json", "graph.v1", None),
        ("models.json", "models.v1", "profiles"),
        ("migration_candidates.json", "migration-candidates.v1", "candidates"),
        ("skill_proposals.json", "skill-proposals.v1", "proposals"),
        ("turn_candidates.json", "turn-candidates.v1", "candidates"),
    ]:
        path = runtime / "stores" / "v2" / name
        if path.exists():
            continue
        if name == "graph.json":
            path.write_text('{\n  "schema_version": "graph.v1",\n  "nodes": {},\n  "edges": []\n}\n')
        elif name == "models.json":
            path.write_text('{\n  "schema_version": "models.v1",\n  "profiles": {\n    "embedding": [],\n    "memory": [],\n    "summarization": [],\n    "skill_evolution": []\n  }\n}\n')
        else:
            default_value = [] if root_key == "candidates" else {}
            path.write_text('{\n  "schema_version": "%s",\n  "%s": %s\n}\n' % (schema_version, root_key, json.dumps(default_value)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    bootstrap(Path(args.workspace).expanduser(), Path(args.repo).expanduser())


if __name__ == "__main__":
    main()
