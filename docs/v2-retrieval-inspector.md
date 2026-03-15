# V2 Retrieval Inspector MVP

This round adds a retrieval inspection backend for OpenClaw Memory V2.

## Components

- `retrieval_inspector.py`
- `AdminAPI.inspect_query(query)`

## Output shape

For a given query, the inspector returns:

- detected route
- per-layer hit counts
- per-layer raw results
- final merged hits

## Why this matters

This is the operational debugging tool needed to answer:

- why was a memory not found?
- which layer matched or failed?
- did routing classify the query correctly?
- did the final result omit useful intermediate hits?

## Follow-up

Next rounds should add:

- scoring details per hit
- alias/synonym expansion traces
- graph expansion traces
- UI panel in the future admin console
