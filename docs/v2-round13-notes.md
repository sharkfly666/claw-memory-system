# V2 Round 13 Notes

This round adds the first write operation for the management console prototype.

## Added

- `POST /api/migration-candidate`
- `AdminAPI.create_migration_candidate_response()`

## Why this matters

This is the first step from a read-mostly console toward a writable management system.

The migration-candidate write flow is a natural first write operation because it is low-risk and directly supports the planned migration studio.
