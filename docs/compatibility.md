# Compatibility Design

Memory storage evolves. Compatibility is not optional.

## Principles

- every persistent store has an explicit version
- migrations are append-only and reviewable
- history is preserved when overwriting truth
- old data is never silently treated as new format

## Facts store

- current format: `version = "1.0"`
- compatibility gate lives in `claw_memory_system.compat`
- unsupported versions fail fast

## Migration policy

When a format changes:
1. add a new schema file (`facts.v2.schema.json`)
2. add a migration script (`migrations/v1_to_v2.py`)
3. keep old readers or explicit upgrade path
4. write migration report for audit

## Forward compatibility ideas

- support per-record schema version when needed
- separate logical version from storage backend version
- keep history entries immutable
