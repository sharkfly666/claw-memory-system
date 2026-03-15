# V2 Round 6 Notes

This round focuses on graph-assisted recall and report solidification.

## Added

- graph-assisted expansion in `search_router.py`
- graph expansion visibility in `retrieval_inspector.py`
- `reports.py` helper for standardized regression reports

## Improvements

- final hits can now be expanded with graph-related nodes
- retrieval inspection now shows how many results came from graph expansion
- realish evaluation now writes a named baseline report into a reports directory

## Why this matters

This moves V2 closer to the intended memory-graph direction and makes regression tracking more operational.
