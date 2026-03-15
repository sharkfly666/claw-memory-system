# Migration Plan

## Goal
Move existing memory into layered storage without polluting current truth.

## Source classes

1. configuration files
2. user/profile files
3. long-term markdown memory
4. daily memory logs
5. existing vector memories

## Migration order

### Phase M1 — inventory
- list sources
- classify candidates
- identify active truth vs historical notes

### Phase M2 — migrate high-confidence facts
- user identity
- current model config
- known service paths
- stable preferences

### Phase M3 — migrate decisions and project state
- produce compact summaries
- keep narrative in markdown
- add exact-search index entries

### Phase M4 — handle legacy vector memory
- keep as semantic layer first
- do not rush full rewrite
- clean and reclassify later

## Rule
Do not mass-copy all old memories into facts.
