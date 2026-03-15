# Webapp Smoke Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Promote the ad-hoc local browser smoke flow into a reusable repository command for Beta verification.

**Architecture:** Add a repo-owned Python CLI that starts the admin HTTP server and static frontend locally, then runs a Playwright browser flow against the real UI. Keep the script self-contained so it does not depend on Codex-only helper paths.

**Tech Stack:** Python CLI scripts, Playwright sync API, local `http.server`, existing admin HTTP runner, Python `unittest`.

### Task 1: Lock the CLI contract

**Files:**
- Create: `tests/test_webapp_smoke_script.py`

**Step 1: Write the failing test**

Assert that `python3 scripts/run_webapp_smoke.py --help` exits successfully and exposes:
- `--workspace`
- `--api-port`
- `--frontend-port`
- `--output-dir`
- `--browser-executable`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_webapp_smoke_script.py'`

Expected: FAIL because the script does not exist yet.

### Task 2: Implement the repo-owned smoke command

**Files:**
- Create: `scripts/run_webapp_smoke.py`

**Step 1: Add minimal implementation**

The script should:
- parse the CLI contract from Task 1
- start `scripts/run_admin_http.py`
- start a static `http.server` for `webapp/`
- wait for both local ports
- run the existing browser smoke flow
- emit JSON result with created ids and screenshot path

**Step 2: Run targeted test**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_webapp_smoke_script.py'`

Expected: PASS

### Task 3: Document and verify

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Step 1: Add a short Beta smoke-test section**

Document the new command and note that it uses a local Chrome if present, otherwise bundled Playwright Chromium.

**Step 2: Run full regression**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

Expected: PASS

**Step 3: Run the repo script for real**

Run the new smoke command against a bootstrapped workspace and confirm the JSON result is `ok: true`.
