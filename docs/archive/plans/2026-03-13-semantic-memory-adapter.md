# Semantic Memory Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a formal semantic memory adapter layer so `claw-memory-system` can wire `memory-lancedb-pro` into the default runtime path and prove provider switching with integration tests.

**Architecture:** Introduce a registry-backed semantic adapter contract in the Python runtime, load the active semantic provider from workspace model profiles, and inject the selected adapter into `SearchRouter` through `AdminAPI.from_workspace()`. Keep exact search ownership unchanged and verify the new provider path with unit tests plus workspace-level integration tests.

**Tech Stack:** Python 3, `unittest`, subprocess-based integration checks, existing workspace bootstrap/runtime wrappers

### Task 1: Add failing adapter contract tests

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_semantic_memory.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_admin_api.py`

**Step 1: Write the failing test**

Add tests for:
- loading no semantic adapter when no memory profile is enabled
- normalizing `memory-lancedb-pro` hits from a configured command-backed adapter
- switching to a different registered provider through the same workspace profile category
- wiring vector hits through `AdminAPI.from_workspace()`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_semantic_memory tests.test_admin_api`
Expected: FAIL because semantic adapter module and default wiring do not exist yet.

**Step 3: Write minimal implementation**

Create the adapter API and only the minimum code needed for those tests to pass.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_semantic_memory tests.test_admin_api`
Expected: PASS

### Task 2: Implement runtime wiring and bootstrap defaults

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/semantic_memory.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/admin_api.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/model_profiles_store.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/bootstrap_openclaw_instance.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/__init__.py`

**Step 1: Write the failing test**

Add or extend tests to assert:
- bootstrap creates a memory provider category in models storage
- the selected semantic adapter is reflected in admin query inspection

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_semantic_memory tests.test_admin_api`
Expected: FAIL because models/bootstrap/default router wiring are incomplete.

**Step 3: Write minimal implementation**

Implement:
- adapter registry + config loader
- `MemoryLanceDBProAdapter`
- active profile selection from `models.json`
- vector query injection into the default admin router

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_semantic_memory tests.test_admin_api`
Expected: PASS

### Task 3: Add integration coverage and docs

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_integration_script.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/scripts/run_openclaw_integration.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/vector-backend.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/vector-backend.zh-CN.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/v2-current-status.md`

**Step 1: Write the failing test**

Add integration-facing tests for:
- semantic adapter checks in the repo-owned integration script
- updated docs/status claims for default runtime adapter wiring

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_integration_script`
Expected: FAIL because the integration script does not expose semantic adapter verification yet.

**Step 3: Write minimal implementation**

Update the integration script and docs to cover the new semantic adapter path without changing the existing exact-search/browser smoke flow.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_openclaw_integration_script`
Expected: PASS

### Task 4: Full verification

**Files:**
- Verify only

**Step 1: Run targeted tests**

Run: `PYTHONPATH=src python3 -m unittest tests.test_semantic_memory tests.test_admin_api tests.test_search_router tests.test_openclaw_integration_script`

**Step 2: Run full suite**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

**Step 3: Run repo integration check**

Run: `python3 scripts/run_openclaw_integration.py --workspace /tmp/openclaw-integration-adapter-check --repo /Users/jiangjk/dev/project/github/claw-memory-system`

**Step 4: Commit**

```bash
git add docs/plans/2026-03-13-semantic-memory-adapter.md \
  src/claw_memory_system/semantic_memory.py \
  src/claw_memory_system/admin_api.py \
  src/claw_memory_system/model_profiles_store.py \
  src/claw_memory_system/bootstrap_openclaw_instance.py \
  src/claw_memory_system/__init__.py \
  scripts/run_openclaw_integration.py \
  tests/test_semantic_memory.py \
  tests/test_admin_api.py \
  tests/test_openclaw_integration_script.py \
  docs/vector-backend.md \
  docs/vector-backend.zh-CN.md \
  docs/v2-current-status.md
git commit -m "feat: add semantic memory adapter runtime"
```
