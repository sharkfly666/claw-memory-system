from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LINE_PATTERNS = [
    (re.compile(r"^\s*- \*\*(.+?)\*\*: (.+)$"), "kv_bold"),
    (re.compile(r"^\s*- \*\*([^*]+)\*\* - (.+)$"), "kv_bold_dash"),
    (re.compile(r"^\s*- ([^:]{1,80}): (.+)$"), "kv_plain"),
]


def scan_markdown(path: Path):
    out = []
    for i, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        for pattern, kind in LINE_PATTERNS:
            m = pattern.match(text)
            if m:
                key = m.group(1).strip()
                value = m.group(2).strip()
                out.append({
                    "source": str(path),
                    "line": i,
                    "kind": kind,
                    "candidate_key": key,
                    "candidate_value": value,
                    "confidence": 0.7 if kind != "kv_plain" else 0.55,
                })
                break
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract fact candidates from markdown files")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = [root / "USER.md", root / "IDENTITY.md", root / "MEMORY.md"]
    files.extend(sorted((root / "memory").glob("*.md")) if (root / "memory").exists() else [])

    candidates = []
    for path in files:
        if path.exists():
            candidates.extend(scan_markdown(path))

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in candidates:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Extracted {len(candidates)} candidates to {out_path}")


if __name__ == "__main__":
    main()
