# Vector Backend

## Recommended default

This project currently recommends **`memory-lancedb-pro`** as the default semantic recall layer when used with OpenClaw.

## Why `memory-lancedb-pro`

It already provides a strong semantic memory baseline for OpenClaw:

- vector retrieval
- BM25 hybrid retrieval
- reranking support
- scope isolation
- good fit for conversation/history recall

## Responsibility split

### `memory-lancedb-pro`
Owns:
- semantic recall
- hybrid retrieval
- reranking
- long-term conversational memory search

### `claw-memory-system`
Owns:
- structured facts
- exact search / page index
- migration tooling
- human-readable memory organization
- time awareness
- compatibility and storage evolution
- routing / orchestration design

## Design principle

This project does **not** currently vendor or merge the source code of `memory-lancedb-pro`.

Instead, it treats it as an external semantic layer.

That keeps boundaries clean:
- vector memory remains specialized
- facts and exact search evolve independently
- OpenClaw integration can stay incremental

## Current integration model

```text
OpenClaw
  ├─ semantic recall -> memory-lancedb-pro
  ├─ exact search    -> claw-memory-system / pageindex
  ├─ facts           -> claw-memory-system / facts
  └─ text memory     -> MEMORY.md / daily memory
```

## Adapter status

This repository now includes a formal semantic adapter path for the default runtime:

- a workspace `memory` profile category in `models.json`
- active-profile selection for semantic providers
- a built-in `MemoryLanceDBProAdapter`
- vector-hit injection into `AdminAPI.from_workspace()` and `SearchRouter`

The built-in adapter uses the `memory-lancedb-pro` CLI entrypoint:

```bash
openclaw memory-pro search "query" --json
```

If needed, a profile can override the command explicitly while keeping the same adapter contract.

Example profile:

```json
{
  "name": "default",
  "provider": "memory-lancedb-pro",
  "enabled": true,
  "active": true,
  "limit": 10,
  "command": [
    "openclaw",
    "memory-pro",
    "search",
    "{query}",
    "--json",
    "--limit",
    "{limit}"
  ]
}
```

## Future direction

Possible next step:
- add more production-grade providers behind the same adapter registry
- normalize score metadata across providers
- later consider hybrid plugin integration if routing stabilizes
