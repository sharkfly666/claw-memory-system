# V2 Round 4 Notes

This round focuses on improving retrieval quality and expanding the admin/service layer.

## Added

- `model_profiles_store.py`
- `migration_candidates_store.py`
- `migration-candidates.v1.schema.json`

## Search improvements

- expanded route classification tokens for preference / task / fact
- task route now also checks sessions and episodes
- fact route now also checks episodes for config/history overlap

## Admin improvements

- `AdminAPI` now exposes model profiles and migration candidates
- added `layer_summary()`
- added `create_migration_candidate()`

## Purpose

These changes move V2 closer to a manageable system:
- better route behavior on realistic queries
- model configuration can now become a first-class managed store
- manual migration workflow has a candidate queue foundation
