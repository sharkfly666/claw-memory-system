# V2 Admin API

This document describes the current OpenClaw Memory V2 admin API surface.

## Current capabilities

- `AdminAPI.from_workspace(workspace_root)`
- `list_layer(layer)`
- `get_record(layer, record_id)`
- `upsert_record(layer, record_id, record)`
- `migrate_record(source_layer, record_id, target_layer, new_id=None)`
- `inspect_query(query)`
- `filter_layer(layer, text=..., status=...)`
- `migration_preview(source_layer, record_id, target_layer, new_id=None)`

## Current HTTP surface

The local HTTP wrapper in `admin_http.py` exposes:

- `GET /api/summary`
- `GET /api/layer?layer=...`
- `GET /api/record?layer=...&id=...`
- `GET /api/inspect?q=...`
- `GET /api/filter?layer=...&text=...&status=...`
- `GET /api/migration-preview?source_layer=...&id=...&target_layer=...`
- `GET /api/report?name=...`
- `POST /api/migration-candidate`
- `POST /api/model-profile`
- `POST /api/skill`
- `POST /api/preference`
- `POST /api/task`
- `POST /api/episode`
- `POST /api/skill-proposal`

## Supported layers

- `facts`
- `preferences`
- `tasks`
- `episodes`
- `skills`
- `sessions`
- `graph.nodes`
- `graph.edges`
- `models`
- `migration_candidates`
- `skill_proposals`

## Current purpose

The admin API now serves two roles:

- in-process service layer for management and inspection logic
- backend for the local management console HTTP endpoints
- manual migration tools
- inspection scripts
- retrieval debugging helpers

## Follow-up

Next rounds should add:

- stronger input validation
- pagination and filtering for large stores
- audit logs for mutation flows
- approval/apply semantics for migration and skill proposal workflows
