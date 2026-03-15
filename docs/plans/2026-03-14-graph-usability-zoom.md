# Graph Usability And Zoom Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the memory graph readable for ordinary users by replacing the piled-up cluster layout with a layered map and by adding zoom/pan/fit controls.

**Architecture:** Keep the existing graph data contract and graph page, but adjust the front-end view model and SVG renderer. Replace the radial cluster layout with a deterministic lane-based memory map, add viewport state for zoom and pan, and expose controls so users can zoom out, reset, and fit the graph to the canvas. Keep the implementation inside `webapp/index.html` and prove behavior with `tests/test_webapp.py`.

**Tech Stack:** Vanilla HTML/CSS/JavaScript, inline SVG, Python `unittest`, Node-based function extraction tests

### Task 1: Add failing tests for viewport controls and layered layout

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Write the failing test**

Add tests that verify:
- the graph page contains zoom controls and a viewport HUD
- the graph view model places nodes into deterministic x lanes by node type instead of a circular cluster
- viewport helpers can zoom in, zoom out, fit, and reset without losing selected-node state

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL because the zoom controls and viewport helpers do not exist yet.

**Step 3: Write minimal implementation**

Add only the smallest markup and helper contracts required for the new tests.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 2: Replace the piled-up graph layout with a layered memory map

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Use failing tests from Task 1**

Keep the suite red while changing the graph geometry.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL with missing or incorrect lane positions.

**Step 3: Write minimal implementation**

Implement:
- type-to-lane x positions
- vertically spaced nodes per lane
- reduced label density for large graphs
- stronger default focus on meaningful memory nodes rather than aliases first

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 3: Add viewport state, zoom, pan, fit, and reset

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Write the failing test**

Add tests that verify:
- `zoomGraphIn`, `zoomGraphOut`, `resetGraphViewport`, and `fitGraphViewport` update viewport state deterministically
- the SVG scene transform reflects viewport state
- `loadGraph()` preserves or reinitializes viewport state correctly

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL because the graph viewport system does not exist yet.

**Step 3: Write minimal implementation**

Add:
- graph viewport state under `graphState`
- toolbar buttons for zoom in, zoom out, fit, reset
- SVG scene group transform updates
- wheel zoom and pointer drag panning

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 4: Sync and verify with the installed plugin

**Files:**
- Modify: `/Users/jiangjk/.openclaw/extensions/claw-memory-system/webapp/index.html` (sync only after repo tests pass)

**Step 1: Run targeted verification**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

**Step 2: Sync installed plugin copy**

Run: `cp /Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html /Users/jiangjk/.openclaw/extensions/claw-memory-system/webapp/index.html`
Expected: installed plugin copy updated with the readable graph map and viewport controls.

**Step 3: Restart gateway**

Run: `/bin/zsh -lc "PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:/opt/homebrew/bin:/usr/bin:/bin openclaw gateway restart"`
Expected: OpenClaw reloads the updated graph UI.

**Step 4: Browser smoke**

Run a Playwright smoke against `file:///Users/jiangjk/.openclaw/extensions/claw-memory-system/webapp/index.html` and verify:
- graph page renders
- zoom controls are present
- graph stats still show non-zero node and edge counts

**Step 5: Commit**

Git commit is intentionally omitted because `/Users/jiangjk/dev/project/github/claw-memory-system` is currently not a git repository.
