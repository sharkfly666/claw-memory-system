# V2 Round 9 Notes

This round adds the first minimal HTTP/app-server layer and connects the webapp shell to real API endpoints.

## Added

- `admin_http.py` WSGI app
- `scripts/run_admin_http.py`
- webapp fetches real JSON from the local admin HTTP API

## API endpoints

- `GET /api/summary`
- `GET /api/layer?layer=...`
- `GET /api/record?layer=...&id=...`
- `GET /api/inspect?q=...`
- `GET /api/filter?layer=...&text=...&status=...`
- `GET /api/migration-preview?source_layer=...&id=...&target_layer=...`

## Why this matters

This is the first point where the V2 admin layer becomes directly consumable by a browser-based management console instead of only Python scripts.
