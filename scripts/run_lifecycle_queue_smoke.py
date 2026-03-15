from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.turn_message_extract import extract_turn_texts
from claw_memory_system.turn_candidate_bridge import TurnCandidateBridge


def main() -> int:
    with TemporaryDirectory() as tmp:
        workspace = Path(tmp) / 'workspace'
        bootstrap(workspace, ROOT)
        messages = [
            {"role": "user", "content": "以后涉及 GitHub 下载优先用 gh"},
            {"role": "assistant", "content": "记住了，后续优先 gh。"},
            {"role": "tool", "content": "updated preference candidate"},
        ]
        texts = extract_turn_texts(messages)
        result = TurnCandidateBridge.from_workspace(workspace, min_confidence=0.88).classify_and_queue(
            user_text=texts['user_text'],
            assistant_text=texts['assistant_text'],
            tool_summary=texts['tool_summary'],
        )
        output = {
            'ok': True,
            'workspace': str(workspace),
            'queued_count': result['queued_count'],
            'queued': result['queued'],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
