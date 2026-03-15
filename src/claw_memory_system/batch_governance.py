from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .admin_api import AdminAPI
from .reports import write_json_report
from .turn_candidates_store import TurnCandidatesStore
from .candidate_conversion import queued_candidate_to_draft


@dataclass
class BatchGovernance:
    workspace_root: Path

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> "BatchGovernance":
        return cls(workspace_root=workspace_root)

    def run(self, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
        api = AdminAPI.from_workspace(self.workspace_root)
        drafts_payload = api.generate_candidate_drafts()
        drafts = drafts_payload.get("drafts", []) if isinstance(drafts_payload, dict) else []

        queued_store = TurnCandidatesStore(self.workspace_root / "memory-system" / "stores" / "v2" / "turn_candidates.json")
        queued_candidates = queued_store.list()
        unique_pending: dict[str, dict[str, Any]] = {}
        for item in queued_candidates:
            if str(item.get("status", "pending")) != "pending":
                continue
            key = str(item.get("dedupe_key", "")) or str(item.get("suggested_id", "")) or str(item.get("summary", ""))
            unique_pending.setdefault(key, item)
        queued_drafts = [queued_candidate_to_draft(item) for item in unique_pending.values()]
        all_drafts = [*drafts, *queued_drafts]

        previews = []
        safe_drafts = []
        conflicted_drafts = []
        applied = []
        noop_count = 0

        for draft in all_drafts:
            preview = api.preview_candidate_draft(draft)
            previews.append(preview)
            if not preview.get("conflicts"):
                safe_drafts.append(draft)
            else:
                same_id_only = all(item.get("type") == "same_id_exists" for item in preview.get("conflicts", []))
                if same_id_only:
                    safe_drafts.append(draft)
                else:
                    conflicted_drafts.append({
                        "draft": draft,
                        "preview": preview,
                    })

        consumed_pending_ids: list[str] = []
        if auto_apply_safe:
            for draft in safe_drafts:
                result = api.apply_candidate_draft(draft, merge_existing=True, supersede_conflicts=False)
                applied.append({
                    "target_layer": draft.get("target_layer"),
                    "target_id": draft.get("target_id"),
                    "result": result,
                })
                if result.get("noop") is True:
                    noop_count += 1
                source_candidate = draft.get("candidate") if isinstance(draft.get("candidate"), dict) else None
                if source_candidate and source_candidate.get("source") == "post-turn-classifier":
                    summary = source_candidate.get("summary")
                    for item in queued_candidates:
                        if item.get("summary") == summary and str(item.get("status", "pending")) == "pending":
                            item["status"] = "consumed"
                            consumed_pending_ids.append(str(item.get("suggested_id", "")))
            if consumed_pending_ids:
                queued_store.save({
                    "schema_version": "turn-candidates.v1",
                    "candidates": queued_candidates,
                })

        graph_summary = None
        if refresh_graph:
            graph_summary = api.refresh_graph()

        governance = api.governance_report()
        summary = {
            "total_drafts": len(all_drafts),
            "generated_drafts": len(drafts),
            "queued_drafts": len(queued_drafts),
            "safe_drafts": len(safe_drafts),
            "conflicted_drafts": len(conflicted_drafts),
            "applied_count": len(applied),
            "noop_count": noop_count,
            "consumed_pending": len(consumed_pending_ids),
            "post_counts": governance.get("structured_counts", {}),
        }

        return {
            "schema_version": "memory-batch-governance.v1",
            "workspace_root": str(self.workspace_root),
            "summary": summary,
            "drafts": drafts_payload,
            "previews": previews,
            "applied": applied,
            "conflicted": conflicted_drafts,
            "graph_summary": graph_summary,
            "governance": governance,
        }

    def write_report(self, path: Path | None = None, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> Path:
        out = path or (self.workspace_root / "memory-system" / "reports" / "memory-batch-governance-report.json")
        write_json_report(self.run(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph), out)
        return out


def run_batch_governance(workspace_root: Path, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> dict[str, Any]:
    return BatchGovernance.from_workspace(workspace_root).run(auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)


def write_batch_governance_report(workspace_root: Path, path: Path | None = None, *, auto_apply_safe: bool = True, refresh_graph: bool = True) -> Path:
    return BatchGovernance.from_workspace(workspace_root).write_report(path, auto_apply_safe=auto_apply_safe, refresh_graph=refresh_graph)
