from __future__ import annotations

import argparse
import json
from pathlib import Path

from .facts_store import FactsStore


def parse_value(raw: str, value_type: str):
    if value_type == "string":
        return raw
    if value_type == "number":
        return float(raw) if "." in raw else int(raw)
    if value_type == "boolean":
        return raw.lower() in {"1", "true", "yes", "on"}
    if value_type in {"array", "object", "null"}:
        return json.loads(raw)
    raise ValueError(f"Unsupported value_type: {value_type}")


def build_store(args) -> FactsStore:
    return FactsStore(Path(args.facts).resolve(), Path(args.history).resolve() if args.history else None)


def main() -> None:
    parser = argparse.ArgumentParser(description="Facts store CLI")
    parser.add_argument("--facts", required=True, help="facts.json path")
    parser.add_argument("--history", help="facts.history.jsonl path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get")
    p_get.add_argument("key")

    p_list = sub.add_parser("list")

    p_set = sub.add_parser("set")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.add_argument("--value-type", required=True, choices=["string", "number", "boolean", "array", "object", "null"])
    p_set.add_argument("--category", default="fact")
    p_set.add_argument("--status", default="active")
    p_set.add_argument("--source", required=True)
    p_set.add_argument("--scope", default="global")
    p_set.add_argument("--aliases", default="")
    p_set.add_argument("--tags", default="")
    p_set.add_argument("--notes")
    p_set.add_argument("--confidence", type=float, default=1.0)

    args = parser.parse_args()
    store = build_store(args)

    if args.cmd == "get":
        fact = store.get_fact(args.key)
        print(json.dumps(fact, ensure_ascii=False, indent=2))
        return

    if args.cmd == "list":
        print(json.dumps(store.list_facts(), ensure_ascii=False, indent=2))
        return

    if args.cmd == "set":
        aliases = [x.strip() for x in args.aliases.split(",") if x.strip()]
        tags = [x.strip() for x in args.tags.split(",") if x.strip()]
        fact = store.upsert_simple(
            args.key,
            parse_value(args.value, args.value_type),
            value_type=args.value_type,
            category=args.category,
            status=args.status,
            source=args.source,
            scope=args.scope,
            aliases=aliases,
            tags=tags,
            notes=args.notes,
            confidence=args.confidence,
        )
        print(json.dumps(fact, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
