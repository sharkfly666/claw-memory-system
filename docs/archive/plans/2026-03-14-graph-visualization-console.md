# Graph Visualization Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the graph page from list-based inspection to a polished, operator-friendly visual memory graph with an industrial Klein-blue interface.

**Architecture:** Keep the existing graph data source and refresh API, but replace the graph page body with a front-end visualization layer built directly in `webapp/index.html`. Use an SVG-based network view with a deterministic layout helper, filter/search controls, KPI cards, and a detail sidebar so ordinary users can inspect graph structure without reading raw JSON lists first.

**Tech Stack:** Vanilla HTML/CSS/JavaScript, inline SVG, existing `unittest` + Node-based webapp tests

### Task 1: Add failing tests for graph visualization scaffolding

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Write the failing test**

Add tests that verify:
- the graph page contains a visualization canvas, graph search input, node-type filter, and graph KPI cards
- a graph view-model helper derives node and edge metrics from API payloads
- `loadGraph()` now renders visual graph state instead of only list state

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL because the new graph UI and helper functions do not exist yet.

**Step 3: Write minimal implementation**

Add only the smallest markup and helper functions needed to satisfy the new tests.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 2: Implement the visual graph stage and layout

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Use failing tests from Task 1**

Keep the suite red while implementing the graph stage.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL with missing visualization helpers or missing DOM targets.

**Step 3: Write minimal implementation**

Implement:
- a graph scene container with SVG nodes and links
- a small deterministic radial/force-like layout helper
- node color and sizing by type/degree
- node selection that updates the existing detail panel
- KPI cards for total nodes, total edges, visible nodes, visible links

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 3: Add user controls and filtering behavior

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Write the failing test**

Add tests that verify:
- graph search filters visible nodes by text
- node-type filter updates visible graph state
- selecting a node updates the relation summary and detail panel

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL because filtering and selection state are not wired yet.

**Step 3: Write minimal implementation**

Add:
- a text search box
- node-type select
- a compact legend / relationship summary
- a filter application step inside `loadGraph()` and the graph render pipeline

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 4: Final verification and runtime sync

**Files:**
- Modify: `/Users/jiangjk/.openclaw/extensions/claw-memory-system/webapp/index.html` (sync only after repo tests pass)

**Step 1: Run targeted verification**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

**Step 2: Sync installed plugin copy**

Run: `cp /Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html /Users/jiangjk/.openclaw/extensions/claw-memory-system/webapp/index.html`
Expected: installed plugin copy updated with the new visual graph UI.

**Step 3: Restart gateway**

Run: `/bin/zsh -lc "PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:/opt/homebrew/bin:/usr/bin:/bin openclaw gateway restart"`
Expected: OpenClaw reloads the plugin and serves the new graph UI.

**Step 4: Smoke-check summary endpoint**

Run: `curl -s http://127.0.0.1:8765/api/summary`
Expected: non-empty graph counts still visible after reload.

**Step 5: Commit**

Git commit is intentionally omitted because `/Users/jiangjk/dev/project/github/claw-memory-system` is currently not a git repository.
