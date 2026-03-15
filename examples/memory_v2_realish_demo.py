from pathlib import Path

from claw_memory_system import (
    EpisodesStore,
    FactsStore,
    GraphStore,
    PreferencesStore,
    SessionStore,
    SkillsStore,
    TasksStore,
)
from claw_memory_system.evaluate_memory import evaluate_cases, load_cases, write_report
from claw_memory_system.search_router import SearchRouter
from claw_memory_system.reports import write_regression_report

base = Path("examples/runtime_realish")
base.mkdir(parents=True, exist_ok=True)

facts_path = base / "facts.json"
prefs_path = base / "preferences.json"
tasks_path = base / "tasks.json"
episodes_path = base / "episodes.json"
skills_path = base / "skills.json"
sessions_path = base / "sessions.json"
graph_path = base / "graph.json"
report_path = base / "report.json"

if not facts_path.exists():
    facts_path.write_text('{\n  "version": "1.0",\n  "facts": {}\n}\n')

facts = FactsStore(facts_path)
prefs = PreferencesStore(prefs_path)
tasks = TasksStore(tasks_path)
episodes = EpisodesStore(episodes_path)
skills = SkillsStore(skills_path)
sessions = SessionStore(sessions_path)
graph = GraphStore(graph_path)

facts.upsert_simple("agent.workspace_path", "/Users/jiangjk/.openclaw/workspace", value_type="string", source="realish-demo")
facts.upsert_simple("memory.minscore", "0.6", value_type="string", source="realish-demo", notes="memory minScore adjusted to 0.6")
facts.upsert_simple("briefing.daily_time", "08:00", value_type="string", source="realish-demo", notes="daily briefing send time")
facts.upsert_simple("service.pansou", "multi cloud search", value_type="string", source="realish-demo", notes="PanSou multi cloud search service")

prefs.upsert("user.communication_style.direct", {
    "value": True,
    "value_type": "boolean",
    "notes": "direct efficient communication",
    "strength": 0.95,
})
prefs.upsert("user.collaboration_style.proactive", {
    "value": True,
    "value_type": "boolean",
    "notes": "proactive autonomous collaboration",
    "strength": 0.9,
})
prefs.upsert("user.profile.technical", {
    "value": True,
    "value_type": "boolean",
    "notes": "technical architecture judgment",
    "strength": 0.88,
})

tasks.upsert("task-memory-eval", {
    "title": "memory evaluation task",
    "summary": "Validate memory loss and compare memos against the old approach.",
    "next_action": "produce diagnosis and upgrade plan",
    "priority": "high",
    "related_entities": ["memos", "memory loss", "old approach"],
})
tasks.upsert("task-briefing-fix", {
    "title": "briefing timeout send failure",
    "summary": "Investigate timeout and send failure in the daily briefing workflow.",
    "next_action": "stabilize transport and retry strategy",
    "priority": "medium",
})

episodes.upsert("ep-memory-validation", {
    "title": "memory loss validation",
    "summary": "Asked to validate whether the new memory system loses memory and whether it is worse than the old approach.",
})
episodes.upsert("ep-gateway-restart", {
    "title": "gateway restart memory config",
    "summary": "Restarted Gateway so the memory minScore configuration would take effect.",
})
episodes.upsert("ep-qwik-eval", {
    "title": "qwik vue2 evaluation",
    "summary": "Concluded Qwik may fit selective high-performance scenarios, while Vue3/Nuxt3 is the safer primary upgrade path for Vue2 teams.",
})
episodes.upsert("ep-memory-redesign", {
    "title": "memory redesign discussion",
    "summary": "Proposed upgrading claw-memory-system into OpenClaw Memory V2 with retention, graph, and admin console ideas.",
})

skills.upsert("skill-memory-eval", {
    "title": "Evaluate memory systems",
    "summary": "Use multi-case tests to compare preference, task, fact, and history recall.",
    "installed": True,
    "quality_score": 0.82,
})

sessions.upsert("main", {
    "active_topics": ["memory evaluation", "memory v2", "qwik evaluation"],
    "active_task_ids": ["task-memory-eval"],
    "recent_decisions": ["upgrade existing claw-memory-system instead of rewriting"],
    "open_questions": ["when to add admin api and console"],
    "next_actions": ["continue v2 implementation"],
})

graph.upsert_node("task-memory-eval", {"node_type": "task", "label": "memory evaluation task"})
graph.upsert_node("ep-memory-validation", {"node_type": "episode", "label": "memory loss validation"})
graph.upsert_node("ep-qwik-eval", {"node_type": "episode", "label": "qwik vue2 evaluation"})
graph.add_edge("task-memory-eval", "summarized_by", "ep-memory-validation")
graph.add_edge("task-memory-eval", "related_to", "ep-qwik-eval")

router = SearchRouter(
    facts=facts,
    preferences=prefs,
    tasks=tasks,
    episodes=episodes,
    sessions=sessions,
    graph=graph,
)

cases = load_cases(Path("examples/eval_cases.memory_v2.realish.json"))
report = evaluate_cases(router, cases)
write_report(report, report_path)
write_regression_report(report, base / 'reports', name='memory_v2_realish_baseline')
print(report)
