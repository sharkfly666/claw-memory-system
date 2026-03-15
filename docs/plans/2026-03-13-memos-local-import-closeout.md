# Memos-Local Import Closeout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repeatable, safety-gated `memos-local` -> `memory-pro` import entrypoint, document the migration procedure, and re-verify the local OpenClaw integration after import.

**Architecture:** Reuse the existing `memos_local_migration` payload builder as the single source of truth, keep preview and actual import as separate CLI entrypoints, and make the real import path require an explicit execute flag. Keep reporting machine-readable so the repo scripts and local verification flow stay scriptable.

**Tech Stack:** Python 3, `argparse`, `subprocess`, `unittest`, existing OpenClaw CLI wrappers

### Task 1: Lock the import workflow with failing tests

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_memos_local_migration.py`

**Step 1: Write the failing test**

Add tests that verify:
- the new actual-import script refuses to run without `--execute`
- the new actual-import script imports once per scope and returns a structured summary

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_memos_local_migration -v`
Expected: FAIL because the actual-import script does not exist yet.

**Step 3: Write minimal implementation**

Create the import entrypoint and only the helper logic needed for per-scope imports and structured output.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_memos_local_migration -v`
Expected: PASS

### Task 2: Add the real import entrypoint

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/memos_local_migration.py`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/scripts/run_memos_local_import.py`

**Step 1: Write the failing test**

Use the tests from Task 1 as the red state.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_memos_local_migration -v`
Expected: FAIL with missing script / missing import summary behavior.

**Step 3: Write minimal implementation**

Implement:
- reusable command execution/parsing helpers in `memos_local_migration.py`
- an import CLI that exports payloads, requires `--execute`, and runs `openclaw memory-pro import` per scope

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_memos_local_migration -v`
Expected: PASS

### Task 3: Document the operator workflow

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/memos-local-migration.zh-CN.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/integrate-memory-lancedb-pro.zh-CN.md`

**Step 1: Write the documentation**

Document:
- `memos-local` vs `memory-pro` distinction
- canonical import rule (`active` only)
- preview, backup, import, and verification commands
- known caveat about skipped short rows

**Step 2: Verify docs against the implemented commands**

Run:
- `python3 scripts/run_memos_local_migration_preview.py --help`
- `python3 scripts/run_memos_local_import.py --help`

Expected: the flags and commands in the docs match the actual scripts.

### Task 4: Final verification

**Files:**
- None

**Step 1: Run repo tests**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`
Expected: PASS

**Step 2: Run the local deep integration check again**

Run: `PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:$PATH python3 scripts/run_openclaw_deep_integration.py --repo /Users/jiangjk/dev/project/github/claw-memory-system --openclaw-home /Users/jiangjk/.openclaw --strict`
Expected: the runtime stays ready after the real memos import.

**Step 3: Commit**

Git commit is intentionally omitted because `/Users/jiangjk/dev/project/github/claw-memory-system` is currently not a git repository.
