from __future__ import annotations

from pathlib import Path
import argparse
import json

from .turn_candidate_bridge import TurnCandidateBridge


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a turn and queue portable pending memory candidates.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--user-text", default="")
    parser.add_argument("--assistant-text", default="")
    parser.add_argument("--tool-summary", default="")
    parser.add_argument("--min-confidence", type=float, default=0.88)
    args = parser.parse_args()

    payload = TurnCandidateBridge.from_workspace(Path(args.workspace).expanduser().resolve(), min_confidence=args.min_confidence).classify_and_queue(
        user_text=args.user_text,
        assistant_text=args.assistant_text,
        tool_summary=args.tool_summary,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
