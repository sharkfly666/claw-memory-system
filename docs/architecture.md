# Architecture

## Layers

1. **Vector recall**
   - semantic memory
   - best for continuation / similar history
   - currently recommended external backend: `memory-lancedb-pro`
   - implemented externally via adapter

2. **Exact search**
   - SQLite FTS5 page index
   - best for model names, paths, config keys, identifiers

3. **Structured facts**
   - current truth store
   - overwrite/update friendly
   - carries explicit metadata and status

4. **Human-readable memory**
   - markdown source of truth for background and narrative

5. **Time awareness**
   - `updated_at`
   - `last_verified`
   - `status`
   - `ttl_days`
   - `superseded_by`

## Query routing

- fact/config question → facts → exact search → vector → text
- history/continuation → vector → exact search → text → facts
- mixed question → facts → vector → exact search → text
