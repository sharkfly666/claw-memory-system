from pathlib import Path
import json

from claw_memory_system import (
    FactsStore,
    PreferencesStore,
    TasksStore,
    EpisodesStore,
    SkillsStore,
    SessionStore,
    GraphStore,
    ModelProfilesStore,
    MigrationCandidatesStore,
)
from claw_memory_system.admin_api import AdminAPI

base = Path("examples/runtime_realish")
api = AdminAPI(
    workspace_root=Path('.'),
    facts=FactsStore(base / 'facts.json'),
    preferences=PreferencesStore(base / 'preferences.json'),
    tasks=TasksStore(base / 'tasks.json'),
    episodes=EpisodesStore(base / 'episodes.json'),
    skills=SkillsStore(base / 'skills.json'),
    sessions=SessionStore(base / 'sessions.json'),
    graph=GraphStore(base / 'graph.json'),
    models=ModelProfilesStore(base / 'models.json'),
    migration_candidates=MigrationCandidatesStore(base / 'migration_candidates.json'),
)

print('summary=')
print(json.dumps(api.layer_summary(), ensure_ascii=False, indent=2))

print('inspect=')
print(json.dumps(api.inspect_query('memory loss validation'), ensure_ascii=False, indent=2))

print('filter episodes=')
print(json.dumps(api.filter_layer('episodes', text='memory'), ensure_ascii=False, indent=2))

print('migration preview=')
print(json.dumps(api.migration_preview('episodes', 'ep-memory-validation', 'tasks', new_id='task-memory-validation'), ensure_ascii=False, indent=2))
