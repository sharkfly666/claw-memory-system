# Structured Graph Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Beta-grade structured-memory graph pipeline so the admin graph view can generate and refresh meaningful nodes and edges from existing structured stores.

**Architecture:** Keep graph persistence in `graph.json`, but add a deterministic builder that derives graph content from structured memory layers only: facts, preferences, tasks, episodes, and sessions. Expose a manual refresh action through `AdminAPI`, `admin_http.py`, and the webapp so operators can rebuild the graph on demand without changing semantic-memory ingestion.

**Tech Stack:** Python 3, `unittest`, existing JSON-backed stores, existing admin WSGI app, vanilla HTML/CSS/JS webapp

### Task 1: Add failing tests for structured graph building

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_graph_builder.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_admin_api.py`

**Step 1: Write the failing test**

Add tests that verify:
- facts become graph nodes with stable labels and metadata
- task `related_entities` produce entity nodes plus `related_to` edges
- episode `task_ids` produce episode-to-task edges
- session `active_task_ids` optionally connect to task nodes
- duplicate aliases/tags/entities do not create duplicate edges or duplicate nodes

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_graph_builder tests.test_admin_api -v`
Expected: FAIL because no graph builder or refresh API exists yet.

**Step 3: Write minimal implementation**

Create only the smallest builder contract needed by the failing tests: deterministic nodes, deterministic edges, dedupe, and graph replacement.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_graph_builder tests.test_admin_api -v`
Expected: PASS

### Task 2: Implement graph rebuild support in backend

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/graph_builder.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/graph_store.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/admin_api.py`

**Step 1: Use failing tests from Task 1**

Keep the suite red while implementing only the missing graph build path.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_graph_builder tests.test_admin_api -v`
Expected: FAIL with missing builder methods or empty graph output.

**Step 3: Write minimal implementation**

Implement:
- a graph builder that reads facts, preferences, tasks, episodes, and sessions
- graph replacement in one save so rebuilds are idempotent
- `AdminAPI.refresh_graph()` plus a response wrapper that returns node and edge counts

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_graph_builder tests.test_admin_api -v`
Expected: PASS

### Task 3: Add HTTP refresh endpoint coverage

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/admin_http.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_admin_http.py`

**Step 1: Write the failing test**

Add a POST endpoint test for `/api/graph/refresh` that verifies:
- status `200`
- response includes `graph_nodes` and `graph_edges`
- a subsequent read of `graph.nodes` / `graph.edges` is non-empty when structured fixtures exist

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_admin_http -v`
Expected: FAIL because the route does not exist yet.

**Step 3: Write minimal implementation**

Add the new POST route and delegate only to `AdminAPI.refresh_graph_response()`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_admin_http -v`
Expected: PASS

### Task 4: Add webapp graph refresh behavior

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/webapp/index.html`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_webapp.py`

**Step 1: Write the failing test**

Add webapp tests that verify:
- graph section exposes a rebuild action
- rebuild action POSTs `/api/graph/refresh`
- rebuild action reloads graph data after success

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: FAIL because there is no rebuild action yet.

**Step 3: Write minimal implementation**

Add a small graph refresh button and JS function that:
- calls `/api/graph/refresh`
- updates a status element with the returned counts
- calls `loadGraph()` after refresh

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_webapp -v`
Expected: PASS

### Task 5: Run final verification

**Files:**
- None

**Step 1: Run targeted suite**

Run: `PYTHONPATH=src python3 -m unittest tests.test_graph_builder tests.test_admin_api tests.test_admin_http tests.test_webapp -v`
Expected: PASS

**Step 2: Rebuild against a real workspace snapshot**

Run: `PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from claw_memory_system.admin_api import AdminAPI

workspace = Path('/Users/jiangjk/.openclaw/workspace')
api = AdminAPI.from_workspace(workspace)
print(api.refresh_graph_response())
PY`
Expected:
- response `ok: True`
- non-zero `graph_nodes`
- non-zero `graph_edges` when structured stores contain usable data

**Step 3: Inspect persisted graph**

Run: `python3 - <<'PY'
from pathlib import Path
import json

path = Path('/Users/jiangjk/.openclaw/workspace/memory-system/stores/v2/graph.json')
data = json.loads(path.read_text())
print({'nodes': len(data.get('nodes', {})), 'edges': len(data.get('edges', []))})
PY`
Expected: non-zero counts after refresh.

**Step 4: Commit**

Git commit is intentionally omitted because `/Users/jiangjk/dev/project/github/claw-memory-system` is currently not a git repository.
