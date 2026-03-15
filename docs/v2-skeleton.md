# V2 Skeleton

This document describes the first-round OpenClaw Memory V2 code skeleton.

## Added stores

- `preferences_store.py`: stable user preferences and collaboration preferences
- `tasks_store.py`: active/paused/done working-memory task records
- `episodes_store.py`: compact summaries of discussions, incidents, and task outcomes
- `skills_store.py`: skill inventory and evolution metadata
- `session_store.py`: per-session active context records
- `graph_store.py`: lightweight node/edge memory graph

## Governance helpers

- `retention.py`: importance, retention policy, lifecycle status, and recommendation helpers

## Added schemas

- `preferences.v1.schema.json`
- `tasks.v1.schema.json`
- `episodes.v1.schema.json`
- `skills.v1.schema.json`
- `session.v1.schema.json`
- `models.v1.schema.json`
- `graph.v1.schema.json`

## Design intent

The V2 skeleton separates long-term memory responsibilities instead of forcing vector recall to do everything.

- Facts remain the source for current truth.
- Preferences capture stable user style and collaboration guidance.
- Tasks hold active working-memory state.
- Episodes remember whole events and discussions.
- Skills track reusable execution knowledge and evolution metadata.
- Session records preserve current-thread context accuracy.
- Graph links provide future association-based recall.

## Current scope

This round intentionally provides only JSON-backed storage and schema skeletons.

Not included yet:

- search router
- extraction pipelines
- admin API
- web console
- evaluation harness
- automated migration flows

These should be added in the next implementation rounds.
