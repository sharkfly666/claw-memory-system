# OpenClaw Memory V2 Skeleton Plan

## Goal
Implement the first-round V2 skeleton without breaking V1.

## Scope
- New JSON-backed stores: preferences, tasks, episodes, skills, session
- Governance helpers: retention, graph store
- New schemas for all new stores and model profiles
- Minimal package export updates
- Doc: V2 skeleton overview

## Constraints
- Preserve existing V1 behavior
- Reuse facts_store patterns where practical
- Keep implementation MVP/simple
- No web UI in this round

## Tasks
1. Inspect current V1 modules and schemas
2. Add reusable metadata/timestamp conventions where needed
3. Implement new store modules
4. Implement retention helpers
5. Implement lightweight graph store
6. Add new schemas
7. Update package exports
8. Add V2 skeleton doc
9. Run basic verification (import/module syntax)

## Verification
- Python compiles new modules
- Imports succeed from package root
- Schemas are valid JSON
