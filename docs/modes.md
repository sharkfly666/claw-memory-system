# Memory Modes

This project supports two practical operating modes when used with OpenClaw.

---

## Option 1 — Full mode (recommended)

Use:
- **`memory-lancedb-pro`** for semantic recall
- **`claw-memory-system`** for facts, exact search, migration, and compatibility

### What you get
- semantic recall
- hybrid retrieval
- reranking
- structured facts
- exact search / page index
- human-readable memory organization
- migration and compatibility framework
- better path toward time-aware memory evolution

### Recommended for
- most OpenClaw users
- users who already rely on long-term semantic recall
- users who want a safer upgrade path instead of a hard switch

### Responsibility split

#### `memory-lancedb-pro`
Owns:
- vector / semantic recall
- BM25 hybrid retrieval
- reranking
- conversation/history similarity search

#### `claw-memory-system`
Owns:
- facts / current truth
- exact search
- migration tooling
- compatibility layer
- human-readable memory structure
- time-awareness design

### Why this is the default recommendation
Because today it gives the best balance:
- mature semantic recall remains available
- current truth becomes more reliable
- exact lookup becomes much stronger
- migration can happen incrementally

---

## Option 2 — Minimal mode

Use:
- **`claw-memory-system` only**
- no `memory-lancedb-pro`

### What you get
- structured facts
- exact search / page index
- human-readable memory
- migration and compatibility tools

### What you do not get
- mature semantic recall
- conversation similarity search
- hybrid vector + BM25 recall from `memory-lancedb-pro`
- good fuzzy “we discussed something like this before” retrieval

### Recommended for
- users who want the simplest and most controllable setup first
- users whose main need is current truth + exact lookup
- users who are okay adding a vector backend later

### Trade-off
This mode is cleaner and simpler, but weaker for historical semantic recall.

---

## Should users skip `memory-lancedb-pro`?

### Short answer
Yes, they can.

### Recommended answer
Not as the default today.

If users skip `memory-lancedb-pro`, they should understand that `claw-memory-system` currently does **not** replace a full semantic memory backend by itself.

So the current recommendation is:

- **default**: `memory-lancedb-pro + claw-memory-system`
- **optional lightweight path**: `claw-memory-system only`

---

## Configuration guidance

### Full mode
Use OpenClaw’s existing semantic memory backend (for example `memory-lancedb-pro`) and bootstrap `claw-memory-system` into the workspace for:
- facts
- exact search
- migration
- compatibility

### Minimal mode
Bootstrap only `claw-memory-system` and rely on:
- facts
- page index
- text memory

Users should expect lower-quality semantic recall until another vector backend is added.

---

## Product direction

The long-term direction should be:

- treat semantic memory as a pluggable backend
- keep facts / exact search / compatibility independent
- later introduce a vector adapter interface

Possible future backends:
- `memory-lancedb-pro`
- `sqlite-vec`
- local embedding backend
- hybrid in-house backend

That is why this project should frame the question as:

> **Choose your semantic memory backend**

not:

> **Do I have to use `memory-lancedb-pro` forever?**
