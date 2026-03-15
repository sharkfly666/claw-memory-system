# OpenClaw Deep Adaptation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a real OpenClaw deep-integration harness that inspects the local OpenClaw runtime, validates semantic/exact/facts wiring, and runs legacy memory migration tests against a workspace.

**Architecture:** Keep `claw-memory-system` as the facts/exact/migration layer, but add a separate real-runtime integration script that targets an installed OpenClaw home/workspace instead of a temporary repo-only fixture. The harness will verify the active memory slot, plugin CLI availability, exact-search wrappers, fact-candidate extraction from legacy markdown memory, and `memory-lancedb-pro` migration/import dry-runs when the CLI is available.

**Tech Stack:** Python 3, `unittest`, subprocess-driven CLI integration, existing OpenClaw workspace wrappers

### Task 1: Add failing tests for a real-runtime integration harness

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_deep_integration.py`

**Step 1: Write the failing test**

Add tests that verify:
- the new script exposes `--openclaw-home`, `--openclaw-bin`, and `--strict`
- a fake OpenClaw runtime can report memory slot state, hook state, exact-search checks, and migration candidate extraction
- a fake `memory-pro` CLI path runs migration and import dry-runs

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration`
Expected: FAIL because the script and runtime helpers do not exist yet.

**Step 3: Write minimal implementation**

Create only the minimum script/runtime helpers required to satisfy the tests.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration`
Expected: PASS

### Task 2: Implement runtime doctor + migration harness

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/openclaw_runtime.py`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/scripts/run_openclaw_deep_integration.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/__init__.py`

**Step 1: Write the failing test**

Extend tests for:
- degraded local state reporting when the active memory slot is not `memory-lancedb-pro`
- migration extraction using workspace wrappers
- `memory-pro migrate check` and `memory-pro import --dry-run` execution when available

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration`
Expected: FAIL because local-state reporting and migration checks are incomplete.

**Step 3: Write minimal implementation**

Implement:
- OpenClaw config inspection
- active memory slot / hook inspection
- `openclaw` CLI probing
- pageindex/facts wrapper verification
- legacy markdown fact-candidate extraction
- optional `memory-pro` migration/import dry-run verification

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration`
Expected: PASS

### Task 3: Run local verification on the installed OpenClaw

**Files:**
- Verify only

**Step 1: Run targeted tests**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_deep_integration tests.test_openclaw_integration_script`

**Step 2: Run full suite**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

**Step 3: Run the real local harness**

Run: `python3 scripts/run_openclaw_deep_integration.py --repo /Users/jiangjk/dev/project/github/claw-memory-system --openclaw-home /Users/jiangjk/.openclaw`

Expected:
- structured report of current active plugin state
- exact/facts wrapper result
- migration extraction result
- migration CLI result or a clear readiness failure

**Step 4: Commit**

```bash
git add docs/plans/2026-03-13-openclaw-deep-adaptation.md \
  src/claw_memory_system/openclaw_runtime.py \
  src/claw_memory_system/__init__.py \
  scripts/run_openclaw_deep_integration.py \
  tests/test_openclaw_deep_integration.py
git commit -m "feat: add deep openclaw integration harness"
```
