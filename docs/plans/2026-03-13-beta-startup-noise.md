# Beta Startup Noise Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove fresh-workspace startup noise in the Beta web console so the first page load does not trigger avoidable browser 404 errors.

**Architecture:** Keep the existing console structure and API semantics intact. Fix the issue at the browser shell by avoiding automatic report fetches on first load when no report is expected, and prevent the default favicon request by embedding an inline icon in the HTML head.

**Tech Stack:** Static HTML/CSS/JS webapp, Python `unittest`, local browser smoke test with Playwright.

### Task 1: Lock the startup expectations with tests

**Files:**
- Modify: `tests/test_webapp.py`
- Test: `tests/test_webapp.py`

**Step 1: Write the failing test**

Add assertions that:
- `webapp/index.html` includes an inline favicon link
- the script bootstrap does not auto-call `loadReport()`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_webapp.py'`

Expected: FAIL because the current page still auto-loads the report and has no inline favicon.

### Task 2: Implement the minimal startup cleanup

**Files:**
- Modify: `webapp/index.html`

**Step 1: Write minimal implementation**

- Add an inline favicon in the `<head>`
- Remove only the automatic `loadReport()` boot call
- Keep the report panel and manual load button unchanged

**Step 2: Run targeted test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_webapp.py'`

Expected: PASS

### Task 3: Regress and verify in a real browser

**Files:**
- Modify if needed: `webapp/index.html`
- Verify: `src/claw_memory_system/admin_http.py`, `tests/test_admin_http.py`

**Step 1: Run full regression**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests`

Expected: PASS

**Step 2: Rerun the local browser smoke test**

Use the existing local backend + static frontend smoke flow and confirm:
- no startup console noise from missing report or favicon
- preference/task/episode write flows still succeed

**Step 3: Record artifacts**

Keep the fresh screenshot in `output/playwright/` for visual confirmation.
