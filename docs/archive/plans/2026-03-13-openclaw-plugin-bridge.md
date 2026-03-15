# OpenClaw Plugin Bridge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Package `claw-memory-system` as an OpenClaw-native tool plugin that can be installed through `openclaw plugins install` while keeping `memory-lancedb-pro` as the active semantic memory backend.

**Architecture:** Add a thin OpenClaw plugin bridge in TypeScript and keep all durable memory logic in the existing Python repo. The plugin will register a small set of tool actions that shell out to repo-owned Python modules/scripts with deterministic path resolution and JSON/text result passthrough.

**Tech Stack:** Python 3.10+, existing repo CLIs/scripts, TypeScript plugin entrypoint for OpenClaw, Python `unittest`.

### Task 1: Add failing plugin package regression tests

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_plugin_bridge.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_package_exports.py`

**Step 1: Write the failing test**

Add tests that assert:
- `openclaw.plugin.json` exists and declares `id = "claw-memory-system"` with `kind = "tool"`.
- `package.json` exists and declares `openclaw.extensions = ["./index.ts"]`.
- plugin/package versions stay in sync.
- bridge metadata advertises the expected tool names.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: FAIL because plugin package files and bridge metadata do not exist yet.

**Step 3: Write minimal implementation**

Create the minimal package files plus any tiny metadata source needed for the tests.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: PASS.

### Task 2: Add a repo-owned Python bridge CLI for plugin tools

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/src/claw_memory_system/openclaw_plugin_bridge.py`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/pyproject.toml`
- Test: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_plugin_bridge.py`

**Step 1: Write the failing test**

Add tests for a Python bridge module that:
- exposes the expected tool names,
- resolves default workspace/runtime paths,
- builds/runs the existing repo commands for bootstrap, facts list/get, build-index, search-index, integration check, and deep integration check.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: FAIL because the module and entrypoints do not exist.

**Step 3: Write minimal implementation**

Implement a small argparse-based bridge CLI that reuses existing repo modules/scripts instead of duplicating logic.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: PASS.

### Task 3: Add the OpenClaw TypeScript plugin entrypoint

**Files:**
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/index.ts`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/openclaw.plugin.json`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/package.json`
- Test: `/Users/jiangjk/dev/project/github/claw-memory-system/tests/test_openclaw_plugin_bridge.py`

**Step 1: Write the failing test**

Extend tests to assert the plugin entrypoint:
- exports a plugin with `kind: "tool"`,
- includes the expected tool ids,
- shells out through the Python bridge module rather than reimplementing logic.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: FAIL because the entrypoint is missing.

**Step 3: Write minimal implementation**

Implement a thin plugin that registers the bridge tools and passes plugin config / tool params into the Python bridge.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
Expected: PASS.

### Task 4: Update docs to prefer plugin install as the standard path

**Files:**
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/README.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/README.zh-CN.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/openclaw-install.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/openclaw-install.zh-CN.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/integrate-memory-lancedb-pro.md`
- Modify: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/integrate-memory-lancedb-pro.zh-CN.md`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/openclaw-plugin-install.md`
- Create: `/Users/jiangjk/dev/project/github/claw-memory-system/docs/openclaw-plugin-install.zh-CN.md`

**Step 1: Write the failing test**

N/A. Documentation task.

**Step 2: Write minimal implementation**

Document:
- local-path plugin installation,
- packaging expectations for npm/archive installs,
- what the plugin currently exposes,
- that `memory-lancedb-pro` remains the memory slot,
- how to use the tools after install.

### Task 5: Verify with repo tests and local OpenClaw install

**Files:**
- No new files required

**Step 1: Run targeted repo tests**

Run:
- `python3 -m unittest tests.test_openclaw_plugin_bridge -v`
- `python3 -m unittest tests.test_bootstrap_openclaw tests.test_openclaw_integration_script tests.test_openclaw_deep_integration -v`

Expected: PASS.

**Step 2: Run full suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS.

**Step 3: Install plugin into local OpenClaw from local path**

Run: `openclaw plugins install /Users/jiangjk/dev/project/github/claw-memory-system`
Expected: install succeeds and plugin appears in `openclaw plugins list`.

**Step 4: Verify host-visible behavior**

Run targeted checks such as:
- `openclaw plugins info claw-memory-system`
- plugin-enabled tool visibility / smoke usage if the host surfaces it

**Step 5: Note environment caveat**

This repo is currently outside git, so there is no commit step for this worktree. Verification output becomes the source of truth for completion.
