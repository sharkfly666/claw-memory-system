# OpenClaw Integration Check Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a reusable repo-owned OpenClaw integration check that bootstraps a workspace, verifies runtime wrappers, and runs the Beta browser smoke path.

**Architecture:** Build one top-level Python CLI that composes existing repo primitives instead of duplicating them. It should bootstrap a workspace, seed `MEMORY.md`, execute the generated wrappers as subprocesses, then call the repo-owned `run_webapp_smoke.py` command and return a single JSON result.

**Tech Stack:** Python CLI scripts, existing bootstrap/runtime wrappers, Playwright smoke command, Python `unittest`.

### Task 1: Lock the CLI contract

**Files:**
- Create: `tests/test_openclaw_integration_script.py`

**Step 1: Write the failing test**

Assert that `python3 scripts/run_openclaw_integration.py --help` exits successfully and exposes:
- `--workspace`
- `--repo`
- `--keep-workspace`
- `--browser-executable`
- `--output-dir`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openclaw_integration_script.py'`

Expected: FAIL because the integration script does not exist yet.

### Task 2: Implement the integration command

**Files:**
- Create: `scripts/run_openclaw_integration.py`

**Step 1: Add minimal implementation**

The script should:
- create or reuse a workspace
- run `bootstrap()`
- seed `MEMORY.md` if needed
- execute the generated facts/pageindex wrappers
- verify exact-search output mentions `memory_md`
- invoke `scripts/run_webapp_smoke.py`
- emit a combined JSON result

**Step 2: Run targeted test**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openclaw_integration_script.py'`

Expected: PASS

### Task 3: Document and verify

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Step 1: Add a short OpenClaw integration-check section**

Document the new command and describe what it verifies.

**Step 2: Run full regression**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

Expected: PASS

**Step 3: Run the integration command for real**

Run the new command against a temporary workspace and confirm the JSON result is `ok: true`.
