# Migrations

Place explicit storage migrations here.

Recommended naming:
- `v1_to_v2.py`
- `facts_v1_to_v2.py`

Each migration should:
1. validate input version
2. write upgraded output
3. preserve history / backup
4. emit a migration report
