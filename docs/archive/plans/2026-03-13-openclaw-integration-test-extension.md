# OpenClaw Integration Test Extension Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the deep OpenClaw integration coverage so the repo verifies parsed migration readiness details, not just subprocess exit codes.

**Architecture:** Keep the existing deep integration harness and fake OpenClaw CLI test fixture, but add parsing for the two noisy human-readable `memory-pro` outputs that matter in real runtime: `migrate check` and `import --dry-run`. Extend tests first so the parsed fields become part of the stable contract of the harness output.

**Tech Stack:** Python 3, `unittest`, subprocess-driven fake CLI fixtures, existing `openclaw_runtime.py`

### Task 1: Add failing tests for parsed migration output

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_deep_integration.py`

**Step 1: Write the failing test**

Add tests that verify:
- noisy `memory-pro version` output still produces a clean semantic version
- `memory-pro migrate check` exposes parsed `legacy_database_found` and `migration_needed`
- `memory-pro import --dry-run` exposes parsed `planned_import_count`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration -v`
Expected: FAIL because the parsed fields are not returned yet.

**Step 3: Write minimal implementation**

Add only the parsing helpers and returned fields required by the tests.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration -v`
Expected: PASS

### Task 2: Parse noisy migration output in the runtime helper

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/openclaw_runtime.py`

**Step 1: Write the failing test**

Use the failing tests from Task 1 as red state.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration -v`
Expected: FAIL with missing parsed fields.

**Step 3: Write minimal implementation**

Implement helpers to parse:
- semantic version from noisy stdout
- `Legacy database found: Yes|No`
- `Migration needed: Yes|No`
- `Would import N memories`

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration -v`
Expected: PASS

### Task 3: Verify the expanded integration contract

**Files:**
- None

**Step 1: Run full suite**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`
Expected: PASS

**Step 2: Run the real local harness**

Run: `PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:$PATH python3 scripts/run_openclaw_deep_integration.py --repo /Users/jiangjk/dev/project/github/claw-memory-system --openclaw-home /Users/jiangjk/.openclaw --strict`
Expected:
- `ready: true`
- parsed migration fields present in the output
- dry-run planned count visible in the output

**Step 3: Commit**

Git commit is intentionally omitted because `/Users/jiangjk/dev/project/github/claw-memory-system` is currently not a git repository.
