# Integrate `memory-lancedb-pro`

This guide explains how to use **`memory-lancedb-pro` + `claw-memory-system`** together in OpenClaw.

## Goal

Use a split-responsibility setup:

- **`memory-lancedb-pro`** handles semantic / hybrid recall
- **`claw-memory-system`** handles facts, exact search, migration, and compatibility

This is the recommended setup today.

---

## What each system does

### `memory-lancedb-pro`
Use it for:
- semantic recall
- hybrid vector + BM25 retrieval
- reranking
- historical conversation similarity

### `claw-memory-system`
Use it for:
- current truth / structured facts
- exact search / page index
- human-readable memory organization
- migration from legacy memory
- time-aware storage evolution

---

## Prerequisites

You need:
- a working OpenClaw installation
- a configured OpenClaw workspace
- `memory-lancedb-pro` available as an OpenClaw plugin
- this repo available locally

---

## Step 1 — Keep `memory-lancedb-pro` as the semantic backend

In OpenClaw, keep your memory plugin slot pointing to `memory-lancedb-pro`.

Conceptually:

```json
{
  "plugins": {
    "slots": {
      "memory": "memory-lancedb-pro"
    }
  }
}
```

> The exact surrounding config may differ depending on your existing OpenClaw setup. The key point is: **do not replace the semantic memory slot yet**.

---

## Step 2 — Install the `claw-memory-system` plugin

Recommended standard path:

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

This plugin exposes facts / exact-search / bootstrap / diagnostic actions, but it does **not** replace the `memory` slot.

---

## Step 3 — Bootstrap `claw-memory-system` runtime into the workspace

Recommended if repo lives outside the workspace:

```bash
cd /path/to/claw-memory-system
./scripts/bootstrap-openclaw.sh ~/.openclaw/workspace
```

Or manually:

```bash
cd /path/to/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo /path/to/claw-memory-system
```

If the repo itself is cloned inside the OpenClaw workspace, that is still supported:

```bash
cd ~/.openclaw/workspace/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/.openclaw/workspace/claw-memory-system
```

---

## Step 4 — Build the exact-search index

```bash
cd ~/.openclaw/workspace
python3 memory-system/index/build_pageindex.py
```

This builds:
- facts index
- `MEMORY.md` index
- `memory/*.md` index

---

## Step 5 — Verify both layers

### Semantic layer (`memory-lancedb-pro`)
Use normal OpenClaw memory recall behavior to confirm semantic recall still works.

### Exact / facts layer (`claw-memory-system`)

```bash
cd ~/.openclaw/workspace
python3 memory-system/facts/facts_cli.py list
python3 memory-system/index/search_pageindex.py "primary model"
```

---

## Recommended workflow

### For semantic / fuzzy history
Use the existing OpenClaw memory flow backed by `memory-lancedb-pro`.

### For current truth / exact lookup
Use `claw-memory-system`:
- facts
- page index
- migration tools
- plugin bridge tools

### For migration
Use:
- `memory-system/migrations/extract_fact_candidates.py`
- `memory-system/facts/facts_cli.py`

---

## Operational model

```text
OpenClaw
  ├─ semantic recall -> memory-lancedb-pro
  ├─ facts           -> claw-memory-system
  ├─ exact search    -> claw-memory-system
  └─ text memory     -> MEMORY.md / daily memory
```

This means you are **augmenting** OpenClaw memory, not replacing it.

---

## Why this is the current recommendation

Because today it gives the best balance:
- you keep proven semantic recall
- you add reliable facts
- you add exact search
- you gain migration and compatibility structure
- you avoid a risky one-shot replacement

---

## Future evolution

Later, if needed, you can move toward:
- automated sidecar synchronization
- vector adapter abstraction
- hybrid memory plugin integration

But for now, the recommended answer is:

> **Keep `memory-lancedb-pro` as the semantic layer, and add `claw-memory-system` as the facts / exact-search / migration layer through the native tool plugin.**
