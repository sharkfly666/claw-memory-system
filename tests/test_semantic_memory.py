from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claw_memory_system.bootstrap_openclaw_instance import bootstrap
from claw_memory_system.model_profiles_store import ModelProfilesStore
from claw_memory_system.semantic_memory import (
    build_semantic_memory_adapter,
    register_semantic_memory_adapter,
    unregister_semantic_memory_adapter,
)


def write_semantic_provider_script(path: Path, *, noisy_stdout: bool = False) -> None:
    noisy_line = 'print("[plugins] memory-lancedb-pro: diagnostic build tag loaded")' if noisy_stdout else ""
    script = """import json
import sys

mode = sys.argv[1]

def emit(payload):
    __NOISY_LINE__
    print(json.dumps(payload))

if mode == "search":
    query = sys.argv[2]
    limit = int(sys.argv[3])
    provider = sys.argv[4]
    payload = [
        {
            "entry": {
                "id": f"{provider}-1",
                "scope": "global",
                "category": "conversation",
                "text": f"{provider} hit for {query}",
                "timestamp": "2026-03-13T00:00:00Z",
                "metadata": {
                    "limit": limit,
                    "provider": provider,
                },
            },
            "score": 0.91,
            "sources": {
                "semantic": 0.87,
                "bm25": 0.44,
            },
        }
    ]
    emit(payload)
elif mode == "stats":
    emit({
        "memory": {
            "totalCount": 7,
            "scopeCounts": {
                "agent:main": 5,
                "global": 2,
            },
            "categoryCounts": {
                "other": 4,
                "fact": 3,
            },
        },
        "retrieval": {
            "mode": "hybrid",
            "hasFtsSupport": True,
        },
    })
elif mode == "list":
    limit = int(sys.argv[2])
    provider = sys.argv[3]
    rows = [
        {
            "id": f"{provider}:recent:1",
            "text": "Recent semantic memory one",
            "scope": "agent:main",
            "category": "other",
            "importance": 0.82,
            "timestamp": 1773394513647,
            "metadata": json.dumps({
                "source": {
                    "plugin": provider,
                }
            }),
        },
        {
            "id": f"{provider}:recent:2",
            "text": "Recent semantic memory two",
            "scope": "global",
            "category": "fact",
            "importance": 0.66,
            "timestamp": 1773394513650,
            "metadata": json.dumps({
                "source": {
                    "plugin": provider,
                }
            }),
        },
    ]
    emit(rows[:limit])
else:
    raise SystemExit(f"unsupported mode: {mode}")
"""
    script = script.replace("__NOISY_LINE__", noisy_line)
    path.write_text(script, encoding="utf-8")


def write_fake_openclaw_script(path: Path) -> None:
    path.write_text(
        """#!/bin/sh
mode="$2"
if [ "$mode" = "search" ]; then
  query="$3"
  limit="$6"
  cat <<EOF
[
  {
    "entry": {
      "id": "fake-openclaw-hit-1",
      "scope": "agent:main",
      "category": "other",
      "text": "fake openclaw hit for ${query}",
      "timestamp": "2026-03-14T00:00:00Z",
      "metadata": {
        "path_head": "${PATH%%:*}",
        "limit": ${limit}
      }
    },
    "score": 0.77,
    "sources": {
      "semantic": 0.77
    }
  }
]
EOF
elif [ "$mode" = "stats" ]; then
  cat <<EOF
{
  "memory": {
    "totalCount": 2,
    "scopeCounts": {
      "agent:main": 2
    },
    "categoryCounts": {
      "other": 2
    }
  },
  "retrieval": {
    "mode": "hybrid",
    "pathHead": "${PATH%%:*}"
  }
}
EOF
elif [ "$mode" = "list" ]; then
  cat <<EOF
[
  {
    "id": "fake-openclaw-recent-1",
    "text": "fake recent memory",
    "scope": "agent:main",
    "category": "other",
    "importance": 0.5,
    "timestamp": 1773394513647,
    "metadata": {
      "path_head": "${PATH%%:*}"
    }
  }
]
EOF
else
  echo "unsupported mode: $mode" >&2
  exit 2
fi
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


class FakeProviderAdapter:
    provider = "fake-provider"

    def __init__(self, workspace_root: Path, profile: dict) -> None:
        self.workspace_root = workspace_root
        self.profile = profile

    def search(self, query: str, *, limit: int | None = None) -> list[dict]:
        return [
            {
                "source": "vector",
                "id": "fake-provider-1",
                "record": {
                    "provider": self.provider,
                    "query": query,
                    "workspace": str(self.workspace_root),
                    "limit": limit,
                },
                "score": 0.55,
            }
        ]


class SemanticMemoryTest(unittest.TestCase):
    def test_build_semantic_memory_adapter_returns_none_without_enabled_profile(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")

            adapter = build_semantic_memory_adapter(workspace, models)

            self.assertIsNone(adapter)

    def test_build_semantic_memory_adapter_normalizes_memory_lancedb_pro_hits(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            script_path = Path(tmp) / "memory_lancedb_pro_provider.py"
            write_semantic_provider_script(script_path)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            models.upsert(
                "memory",
                "default",
                {
                    "provider": "memory-lancedb-pro",
                    "enabled": True,
                    "active": True,
                    "command": [sys.executable, str(script_path), "search", "{query}", "{limit}", "memory-lancedb-pro"],
                    "stats_command": [sys.executable, str(script_path), "stats"],
                    "list_command": [sys.executable, str(script_path), "list", "{limit}", "memory-lancedb-pro"],
                },
            )

            adapter = build_semantic_memory_adapter(workspace, models)

            self.assertIsNotNone(adapter)
            hits = adapter.search("semantic memory", limit=3)
            self.assertEqual(hits[0]["source"], "vector")
            self.assertEqual(hits[0]["id"], "memory-lancedb-pro-1")
            self.assertEqual(hits[0]["score"], 0.91)
            self.assertEqual(hits[0]["record"]["provider"], "memory-lancedb-pro")
            self.assertEqual(hits[0]["record"]["text"], "memory-lancedb-pro hit for semantic memory")
            self.assertEqual(hits[0]["record"]["metadata"]["limit"], 3)

            overview = adapter.overview(limit=2)
            self.assertEqual(overview["provider"], "memory-lancedb-pro")
            self.assertEqual(overview["total_count"], 7)
            self.assertEqual(overview["scope_counts"]["agent:main"], 5)
            self.assertEqual(overview["category_counts"]["fact"], 3)
            self.assertEqual(overview["retrieval"]["mode"], "hybrid")
            self.assertEqual(len(overview["recent"]), 2)
            self.assertEqual(overview["recent"][0]["metadata"]["source"]["plugin"], "memory-lancedb-pro")

    def test_build_semantic_memory_adapter_switches_to_registered_provider(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            models.upsert(
                "memory",
                "alternate",
                {
                    "provider": "fake-provider",
                    "enabled": True,
                    "active": True,
                },
            )

            register_semantic_memory_adapter("fake-provider", FakeProviderAdapter)
            try:
                adapter = build_semantic_memory_adapter(workspace, models)
                self.assertIsNotNone(adapter)
                hits = adapter.search("switch provider", limit=5)
            finally:
                unregister_semantic_memory_adapter("fake-provider")

            self.assertEqual(hits[0]["record"]["provider"], "fake-provider")
            self.assertEqual(hits[0]["record"]["query"], "switch provider")
            self.assertEqual(hits[0]["record"]["limit"], 5)

    def test_build_semantic_memory_adapter_parses_json_after_leading_logs(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            script_path = Path(tmp) / "memory_lancedb_pro_provider.py"
            write_semantic_provider_script(script_path, noisy_stdout=True)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            models.upsert(
                "memory",
                "default",
                {
                    "provider": "memory-lancedb-pro",
                    "enabled": True,
                    "active": True,
                    "command": [sys.executable, str(script_path), "search", "{query}", "{limit}", "memory-lancedb-pro"],
                    "stats_command": [sys.executable, str(script_path), "stats"],
                    "list_command": [sys.executable, str(script_path), "list", "{limit}", "memory-lancedb-pro"],
                },
            )

            adapter = build_semantic_memory_adapter(workspace, models)

            self.assertIsNotNone(adapter)
            hits = adapter.search("semantic memory", limit=2)
            overview = adapter.overview(limit=1)

            self.assertEqual(hits[0]["record"]["text"], "memory-lancedb-pro hit for semantic memory")
            self.assertEqual(overview["total_count"], 7)
            self.assertEqual(overview["recent"][0]["text"], "Recent semantic memory one")

    def test_build_semantic_memory_adapter_prepends_openclaw_bin_directory_to_path(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            bootstrap(workspace, ROOT)
            fake_bin_dir = Path(tmp) / "fake-openclaw-bin"
            fake_bin_dir.mkdir()
            fake_openclaw = fake_bin_dir / "openclaw"
            write_fake_openclaw_script(fake_openclaw)
            models = ModelProfilesStore(workspace / "memory-system" / "stores" / "v2" / "models.json")
            models.upsert(
                "memory",
                "default",
                {
                    "provider": "memory-lancedb-pro",
                    "enabled": True,
                    "active": True,
                    "openclaw_bin": str(fake_openclaw),
                },
            )

            adapter = build_semantic_memory_adapter(workspace, models)

            self.assertIsNotNone(adapter)
            hits = adapter.search("path check", limit=3)
            overview = adapter.overview(limit=1)

            self.assertEqual(hits[0]["record"]["metadata"]["path_head"], str(fake_bin_dir))
            self.assertEqual(overview["retrieval"]["pathHead"], str(fake_bin_dir))
            self.assertEqual(overview["recent"][0]["metadata"]["path_head"], str(fake_bin_dir))


if __name__ == "__main__":
    unittest.main()
