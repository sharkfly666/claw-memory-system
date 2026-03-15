# Install Into OpenClaw

Plugin installation is now the preferred path.

If you want the old direct bootstrap-only flow, it is still supported further below.

This project is designed for a **code/data split**:

- **Code repo** lives anywhere you want (for example cloned from GitHub)
- **Data instance** lives inside an OpenClaw workspace at `memory-system/`

This avoids mixing generated data with source code.

## Recommended layout

```text
~/.openclaw/workspace/
├── memory-system/           # data instance
│   ├── code -> /path/to/claw-memory-system
│   ├── facts/
│   ├── index/
│   ├── migrations/
│   └── receipts/
└── ... other workspace files

/path/to/claw-memory-system/ # cloned repo or plugin source
```

## Preferred path — install as a native plugin

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

Then bootstrap the workspace runtime once:

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_bootstrap \
  --workspace ~/.openclaw/workspace
```

After that, continue with:

```bash
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_build_index \
  --workspace ~/.openclaw/workspace

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_search_index \
  --workspace ~/.openclaw/workspace \
  --query "primary model"
```

## Direct bootstrap path — repo cloned outside the workspace

```bash
git clone https://github.com/<you>/claw-memory-system.git ~/dev/project/github/claw-memory-system
cd ~/dev/project/github/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/dev/project/github/claw-memory-system
```

## Direct bootstrap path — repo cloned inside the OpenClaw workspace

If a user clones this repo into the OpenClaw workspace itself, for example:

```text
~/.openclaw/workspace/claw-memory-system
```

that is still supported. Run:

```bash
cd ~/.openclaw/workspace/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/.openclaw/workspace/claw-memory-system
```

This will still create a separate runtime data directory:

```text
~/.openclaw/workspace/memory-system
```

So even when the repo is physically inside the workspace, **code and runtime data remain separated logically**.

## After bootstrap

Use the workspace wrappers:

```bash
cd ~/.openclaw/workspace
python3 memory-system/index/build_pageindex.py
python3 memory-system/index/search_pageindex.py "primary model"
python3 memory-system/facts/facts_cli.py list
```

## Notes

- Current vector recall is expected to remain external (for example `memory-lancedb-pro`).
- This project currently provides facts + exact search + migration tooling + compatibility structure.
- The new plugin package is a tool bridge. It does not replace the semantic memory slot.
- For plugin-first installation details, see `docs/openclaw-plugin-install.md`.
