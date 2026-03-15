# Install As An OpenClaw Plugin

`claw-memory-system` now supports a native OpenClaw plugin package.

This is the **preferred standard installation path** when you want OpenClaw to discover and expose the project through its plugin system.

## What this plugin does

The plugin is a **tool bridge**, not a replacement memory backend.

It exposes repo-owned actions for:

- workspace bootstrap
- exact-search index build
- exact-search lookup
- facts list / get
- integration check
- deep local integration + migration check

It intentionally does **not** replace the OpenClaw `memory` slot.

## Keep the semantic memory slot unchanged

Keep `memory-lancedb-pro` as the active semantic memory backend:

```json
{
  "plugins": {
    "slots": {
      "memory": "memory-lancedb-pro"
    }
  }
}
```

Use `claw-memory-system` for facts, exact lookup, migration, and diagnostics.

## Install from a local path

From the repo root:

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

If your OpenClaw version auto-enables plugins during install, the explicit `enable` command is harmless.

## If install reports an allowlist error

On the local OpenClaw build verified on March 13, 2026, `install` could finish copying the plugin into `~/.openclaw/extensions/` and still fail during the same command's allowlist update step.

If that happens:

```bash
openclaw plugins info claw-memory-system
openclaw plugins enable claw-memory-system
```

If `info` already sees the plugin source under `~/.openclaw/extensions/claw-memory-system`, the copy succeeded and `enable` is the follow-up step that finishes activation.

## Bootstrap the workspace runtime

After the plugin is installed, bootstrap the runtime data instance once:

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_bootstrap \
  --workspace ~/.openclaw/workspace
```

This creates the `memory-system/` runtime tree inside the workspace.

By default, the plugin also bootstraps the workspace and auto-starts the local admin HTTP process when the OpenClaw gateway starts. The console is available at:

```text
http://127.0.0.1:18789/plugins/claw-memory-system
```

If you sync new plugin code into `~/.openclaw/extensions/claw-memory-system` while the gateway is already running, restart it once:

```bash
openclaw gateway restart
```

That is required for newly added service or route registration logic to take effect. You should not need to start the admin backend manually unless `autoStartAdmin` is explicitly set to `false`. Override `adminHost`, `adminPort`, or `autoStartAdmin` only when you need custom runtime behavior.

## Minimum readiness checklist

For normal OpenClaw usage, verify these commands:

```bash
openclaw plugins info claw-memory-system
openclaw memory-pro stats --scope agent:main --json
openclaw agent --session-id claw-memory-ready-check \
  --message "Call claw_memory_integration_check with skip_smoke=true. Return only compact JSON with ok, semantic_provider, vector_hits, and used_tools." \
  --json
```

Treat the setup as ready when:

- `claw-memory-system` shows `Status: loaded`
- `memory-lancedb-pro` remains the active `plugins.slots.memory` target
- `openclaw memory-pro stats` returns normal counts
- the agent turn returns `"ok": true` and `"semantic_provider": "memory-lancedb-pro"`

You do not need extra config for `claw-memory-system` in the common case. Add `plugins.entries.claw-memory-system.config` only when you need to override `pythonBin`, `repoPath`, `workspaceDir`, `openclawHome`, or `openclawBin`.

If you keep editing the repo after installing from a local path, remember that OpenClaw executes the copied extension under `~/.openclaw/extensions/claw-memory-system`. Reinstall or resync that copy when you want the host to use the latest repo code.

## Typical follow-up commands

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_build_index \
  --workspace ~/.openclaw/workspace

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_search_index \
  --workspace ~/.openclaw/workspace \
  --query "primary model"

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_facts_list \
  --workspace ~/.openclaw/workspace
```

## What OpenClaw can install directly

The local `openclaw plugins install --help` output describes accepted sources as:

- local path
- archive file
- npm package spec

That means a plain GitHub repo URL is **not** the safest assumption for direct installation.

If you want remote installs, package this repo as either:

- an npm package
- a `.zip` / `.tgz` / `.tar.gz` archive

## Legacy bootstrap path

Direct bootstrap without plugin installation is still supported:

```bash
./scripts/bootstrap-openclaw.sh ~/.openclaw/workspace
```

Use that path when you are developing the repo locally and do not need OpenClaw-native plugin discovery.

## Optional deeper verification

The repo also provides:

```bash
python3 scripts/run_openclaw_integration.py --workspace ~/.openclaw/workspace
```

That command includes the Beta browser smoke path. If your current Python environment does not have `playwright`, the smoke step will fail even if the host setup is already usable. In that case, rely on the readiness checklist above for daily validation.
