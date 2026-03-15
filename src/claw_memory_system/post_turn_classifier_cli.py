from __future__ import annotations

from pathlib import Path
import argparse
import json

from .post_turn_classifier import classify_turn


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a turn for autonomous memory handling.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--user-text", default="")
    parser.add_argument("--assistant-text", default="")
    parser.add_argument("--tool-summary", default="")
    args = parser.parse_args()

    payload = classify_turn(
        Path(args.workspace).expanduser().resolve(),
        user_text=args.user_text,
        assistant_text=args.assistant_text,
        tool_summary=args.tool_summary,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
