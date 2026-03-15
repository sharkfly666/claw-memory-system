from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .episodes_store import EpisodesStore
from .facts_store import FactsStore
from .memory_governance import MemoryGovernance
from .preferences_store import PreferencesStore
from .tasks_store import TasksStore


@dataclass
class MemoryMigrator:
    workspace_root: Path
    facts: FactsStore
    preferences: PreferencesStore
    tasks: TasksStore
    episodes: EpisodesStore

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "MemoryMigrator":
        root = workspace_root / "memory-system"
        return cls(
            workspace_root=workspace_root,
            facts=FactsStore(root / "facts" / "facts.json", root / "facts" / "facts.history.jsonl"),
            preferences=PreferencesStore(root / "stores" / "v2" / "preferences.json"),
            tasks=TasksStore(root / "stores" / "v2" / "tasks.json"),
            episodes=EpisodesStore(root / "stores" / "v2" / "episodes.json"),
        )

    def bootstrap_core_records(self) -> dict[str, Any]:
        applied = {
            "preferences": [],
            "tasks": [],
            "episodes": [],
            "facts": [],
        }

        pref_records = {
            "user.communication_style": {
                "summary": "用户偏好直接、高效、少废话的沟通方式。",
                "scope": "global",
                "importance": "high",
                "status": "active",
                "aliases": ["直接一点", "少废话", "高效沟通", "老大喜欢直接高效"],
                "tags": ["communication", "style"],
                "evidence": "USER.md + SOUL.md",
                "notes": "默认回答应简洁、直接、少套话。",
            },
            "user.github_download_preference": {
                "summary": "涉及 GitHub 代码下载或拉取时，优先使用 gh 而不是 git clone。",
                "scope": "global",
                "importance": "high",
                "status": "active",
                "aliases": ["GitHub 下载优先 gh", "用 gh 不用 git clone"],
                "tags": ["tooling", "github"],
                "evidence": "existing memory preference",
                "notes": "其它场景保持现状。",
            },
            "agent.forbidden_qclaw_paths": {
                "summary": "不要再尝试访问或查找任何 QClaw 本地路径。",
                "scope": "global",
                "importance": "high",
                "status": "active",
                "aliases": ["不要访问 QClaw 路径", "QClaw 已卸载"],
                "tags": ["environment", "safety", "path"],
                "evidence": "existing memory preference",
                "notes": "后续仅使用 ~/.openclaw 与 workspace 路径。",
            },
            "user.storage_lifecycle_preference": {
                "summary": "生成文件按长/中/短/临时保存周期分类，优先带日期命名。",
                "scope": "global",
                "importance": "high",
                "status": "active",
                "aliases": ["生成文件分桶保存", "按保存周期规整分类"],
                "tags": ["storage", "generated-files"],
                "evidence": "existing memory preference + AGENTS.md",
                "notes": "明显临时文件默认放 generated/temp。",
            },
            "user.pansou_search_preference": {
                "summary": "PanSou 搜索优先 Quark、优先最新资源、优先有效链接，并使用 API-first 的镜像顺序。",
                "scope": "global",
                "importance": "high",
                "status": "active",
                "aliases": ["PanSou 优先夸克", "优先最新有效资源", "PanSou 镜像优先级"],
                "tags": ["pansou", "search", "resource", "config"],
                "evidence": "技能规则 + 已更新记忆",
                "notes": "镜像顺序由 facts 层保存；本条保存搜索偏好规则。",
            },
        }
        for key, record in pref_records.items():
            self.preferences.upsert(key, record)
            applied["preferences"].append(key)

        fact_updates = {
            "pansou.mirror_priority": {
                "value": [
                    "https://www.daiyazhi.com/api/search",
                    "https://s.panhunt.com/api/search",
                    "https://ps.252035.xyz/api/search",
                    "http://38.55.131.86:82/api/search",
                ],
                "value_type": "array",
                "source": "memory migration bootstrap",
                "tags": ["pansou", "config", "mirror"],
                "aliases": ["PanSou 镜像优先级", "pansou mirror priority"],
                "notes": "Current API-first mirror order.",
            },
            "pansou.token_file": {
                "value": str(self.workspace_root / "memory" / "pansou-token.json"),
                "value_type": "string",
                "source": "memory migration bootstrap",
                "tags": ["pansou", "auth", "path"],
                "aliases": ["PanSou token 文件", "pansou-token.json"],
                "notes": "Authenticated fallback token file path.",
            },
            "daily_briefing.schedule": {
                "value": "每天 08:00",
                "value_type": "string",
                "source": "memory migration bootstrap",
                "tags": ["daily-briefing", "schedule", "config"],
                "aliases": ["早报发送时间", "daily briefing 8:00"],
                "notes": "Current target schedule for daily briefing.",
            },
        }
        for key, cfg in fact_updates.items():
            self.facts.upsert_simple(
                key,
                cfg["value"],
                value_type=cfg["value_type"],
                source=cfg["source"],
                aliases=cfg["aliases"],
                tags=cfg["tags"],
                notes=cfg["notes"],
            )
            applied["facts"].append(key)

        task_records = {
            "task.daily-briefing-stability": {
                "title": "提升 daily-briefing 稳定性",
                "summary": "持续优化超时、Feishu 投递、内容收敛与可用性。",
                "goal": "让 daily-briefing 稳定按时产出并安全送达。",
                "next_step": "继续清理数据源与投递链路，并沉淀结构化记忆。",
                "blockers": [],
                "priority": "high",
                "related_entities": ["daily-briefing", "feishu", "marketwatch"],
                "aliases": ["早报稳定性", "daily briefing timeout"],
                "tags": ["daily-briefing", "automation", "feishu"],
                "importance": "high",
                "state": "active",
                "owner_scope": "global",
            },
            "task.claw-memory-layering": {
                "title": "完善记忆分层与治理能力",
                "summary": "让 preferences / tasks / episodes 真正接管长期协作记忆。",
                "goal": "补齐治理报告、候选迁移、分层写入规范与真实迁移流程。",
                "next_step": "继续把候选自动迁成结构化记录，并补冲突治理。",
                "blockers": [],
                "priority": "high",
                "related_entities": ["claw-memory-system", "OpenClaw", "memory governance"],
                "aliases": ["记忆分层", "memory governance", "memory layering"],
                "tags": ["memory", "governance", "migration"],
                "importance": "high",
                "state": "active",
                "owner_scope": "global",
            },
        }
        for task_id, record in task_records.items():
            self.tasks.upsert(task_id, record)
            applied["tasks"].append(task_id)

        episode_records = {
            "episode.disable-autorecall-2026-03": {
                "title": "关闭 autoRecall 以降低噪声",
                "summary": "因低相关记忆反复注入系统消息，最终关闭 autoRecall，改为手动/定时 recall。",
                "episode_type": "decision",
                "decision": "暂时关闭 autoRecall",
                "impact": "减少低相关噪声，但需要主动 recall。",
                "related_task_ids": ["task.claw-memory-layering"],
                "aliases": ["关闭 autoRecall", "memory autoRecall 噪声"],
                "tags": ["memory", "retrieval", "noise"],
                "importance": "high",
                "status": "active",
            },
            "episode.pansou-mirror-migration-2026-03": {
                "title": "PanSou 镜像顺序迁移",
                "summary": "PanSou 从旧镜像顺序迁到 daiyazhi -> panhunt -> ps.252035.xyz -> 38.55.131.86。",
                "episode_type": "change",
                "decision": "更换默认首选镜像，并加入第 4 个镜像。",
                "impact": "降低对单一认证方案的依赖，提升搜索稳定性。",
                "related_fact_keys": ["pansou.mirror_priority"],
                "aliases": ["PanSou 镜像切换", "新增第4镜像"],
                "tags": ["pansou", "migration", "mirror"],
                "importance": "high",
                "status": "active",
            },
            "episode.daily-briefing-fixes-2026-03": {
                "title": "daily-briefing 三月修复",
                "summary": "三月期间围绕超时、Feishu 审核、投递与财经数据源做了多轮修复与收敛。",
                "episode_type": "maintenance",
                "decision": "继续收紧提示词、优化投递与数据源选择。",
                "impact": "早报可用性提升，但仍需持续治理。",
                "related_task_ids": ["task.daily-briefing-stability"],
                "aliases": ["早报修复", "daily-briefing timeout fix"],
                "tags": ["daily-briefing", "feishu", "timeout"],
                "importance": "high",
                "status": "active",
            },
        }
        for episode_id, record in episode_records.items():
            self.episodes.upsert(episode_id, record)
            applied["episodes"].append(episode_id)

        return applied

    def write_bootstrap_report(self, path: Path | None = None) -> Path:
        out = path or (self.workspace_root / "memory-system" / "reports" / "memory-bootstrap-report.json")
        data = {
            "schema_version": "memory-bootstrap-report.v1",
            "workspace_root": str(self.workspace_root),
            "applied": self.bootstrap_core_records(),
            "post_governance": MemoryGovernance.from_workspace(self.workspace_root).build_report(),
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return out


def bootstrap_core_memory_records(workspace_root: Path) -> dict[str, Any]:
    return MemoryMigrator.from_workspace(workspace_root).bootstrap_core_records()


def write_memory_bootstrap_report(workspace_root: Path, path: Path | None = None) -> Path:
    return MemoryMigrator.from_workspace(workspace_root).write_bootstrap_report(path)
