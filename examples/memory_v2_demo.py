from pathlib import Path

from claw_memory_system import (
    EpisodesStore,
    FactsStore,
    GraphStore,
    PreferencesStore,
    SessionStore,
    TasksStore,
)
from claw_memory_system.evaluate_memory import evaluate_cases, load_cases
from claw_memory_system.search_router import SearchRouter

base = Path("examples/runtime")
base.mkdir(parents=True, exist_ok=True)

facts_path = base / "facts.json"
prefs_path = base / "preferences.json"
tasks_path = base / "tasks.json"
episodes_path = base / "episodes.json"
sessions_path = base / "sessions.json"
graph_path = base / "graph.json"

if not facts_path.exists():
    facts_path.write_text('{\n  "version": "1.0",\n  "facts": {}\n}\n')

facts = FactsStore(facts_path)
prefs = PreferencesStore(prefs_path)
tasks = TasksStore(tasks_path)
episodes = EpisodesStore(episodes_path)
sessions = SessionStore(sessions_path)
graph = GraphStore(graph_path)

facts.upsert_simple(
    "agent.workspace_path",
    "/Users/jiangjk/.openclaw/workspace",
    value_type="string",
    source="demo",
    notes="Default OpenClaw workspace path",
)
prefs.upsert("user.communication_style.direct", {
    "value": True,
    "value_type": "boolean",
    "notes": "User prefers direct and efficient communication",
    "strength": 0.95,
})
tasks.upsert("task-memory-v2", {
    "title": "Build OpenClaw Memory V2 skeleton",
    "summary": "Implement layered stores, retention helpers, graph store, and search router.",
    "next_action": "Add admin API and migration tools",
    "priority": "high",
})
episodes.upsert("ep-memory-discussion", {
    "title": "Memory system redesign discussion",
    "summary": "Compared MemOS and prior approach, then proposed layered V2 architecture.",
})
sessions.upsert("main", {
    "active_topics": ["memory v2", "search router", "evaluation"],
    "active_task_ids": ["task-memory-v2"],
    "recent_decisions": ["upgrade existing claw-memory-system instead of rewriting"],
    "open_questions": ["when to add admin api"],
    "next_actions": ["implement second round"],
})
graph.upsert_node("task-memory-v2", {"node_type": "task", "label": "Build OpenClaw Memory V2 skeleton"})
graph.upsert_node("ep-memory-discussion", {"node_type": "episode", "label": "Memory redesign discussion"})
graph.add_edge("task-memory-v2", "summarized_by", "ep-memory-discussion")

router = SearchRouter(
    facts=facts,
    preferences=prefs,
    tasks=tasks,
    episodes=episodes,
    sessions=sessions,
    graph=graph,
)

cases = load_cases(Path("examples/eval_cases.memory_v2.demo.json"))
report = evaluate_cases(router, cases)
print(report)
