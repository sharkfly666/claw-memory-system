# Release The OpenClaw Plugin

This guide explains the standard release paths for `claw-memory-system` once the repo is published.

## Important distinction

Publishing this repo to GitHub is **not the same thing** as making it directly installable by OpenClaw.

As verified locally on March 13, 2026, `openclaw plugins install` expects one of these source types:

- a local path
- an archive file
- an npm package spec

That means a plain GitHub repo URL should **not** be treated as the default install path.

## Recommended public install channels

Use one or both of these channels for standard public distribution:

### Option A: npm package

Publish the plugin package to npm, then install with a package spec:

```bash
openclaw plugins install claw-memory-system@0.1.0
openclaw plugins enable claw-memory-system
```

This is the cleanest end-user path if you want OpenClaw to install the plugin without asking users to clone the repo first.

### Option B: GitHub Release archive

Create a release asset such as `claw-memory-system-0.1.0.tgz` or `.zip`, then let users download it and install from the local archive:

```bash
openclaw plugins install /path/to/claw-memory-system-0.1.0.tgz
openclaw plugins enable claw-memory-system
```

This is a good path when you want a reproducible artifact but do not want to publish to npm yet.

## Local development install still works

For local development or source-based evaluation:

```bash
git clone <repo>
cd claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
```

This remains the simplest developer path, but it is not the same thing as a remote install flow.

## Packaging status in this repo

The repo is currently packaged as an OpenClaw plugin with:

- [`package.json`](../package.json)
- [`openclaw.plugin.json`](../openclaw.plugin.json)
- the plugin entrypoint [`index.ts`](../index.ts)
- Python runtime files under [`src/claw_memory_system`](../src/claw_memory_system)
- bridge/runtime scripts under [`scripts`](../scripts)

The npm package whitelist has been narrowed so release artifacts include runtime source files but exclude Python bytecode cache directories.

## Release checklist

Use this checklist before publishing:

1. Bump the version in [`package.json`](../package.json) and [`openclaw.plugin.json`](../openclaw.plugin.json).
2. Verify the package contents:

```bash
PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:$PATH \
npm_config_cache=/tmp/claw-memory-system-npm-cache \
npm pack --dry-run --json
```

3. Run repo regression tests:

```bash
python3 -m unittest discover -s tests -v
```

4. Publish one of these artifacts:
- npm package: `claw-memory-system@<version>`
- archive asset: `claw-memory-system-<version>.tgz` or `.zip`

5. Verify installability with a real host:

```bash
openclaw plugins install <local-path-or-package-spec>
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

6. Run the minimum readiness check:

```bash
openclaw memory-pro stats --scope agent:main --json
openclaw agent --session-id claw-memory-ready-check \
  --message "Call claw_memory_integration_check with skip_smoke=true. Return only compact JSON with ok, semantic_provider, vector_hits, and used_tools." \
  --json
```

## After install

Keep the OpenClaw semantic memory slot on `memory-lancedb-pro`.

`claw-memory-system` is a tool plugin bridge. It complements semantic memory with:

- facts
- exact lookup
- migration tooling
- runtime diagnostics

## What to tell end users

The simplest accurate guidance is:

- If you cloned the repo locally, install from the local path.
- If you want standard remote installs, use the npm package or a release archive.
- Do not assume OpenClaw can install directly from a raw GitHub repo URL.
