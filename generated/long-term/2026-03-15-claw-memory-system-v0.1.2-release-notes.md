# claw-memory-system v0.1.2

Patch release focused on final quickstart polish, language-switch entry points, and install guidance for new OpenClaw users.

## What changed
- added language switch entry points between `README.md` and `README.zh-CN.md`
- improved root README quickstart so users can install and bootstrap directly from the top-level docs
- clarified the tested stack and recommended OpenClaw version (`2026.3.12+`)
- documented `plugins.allow` guidance for environments using explicit allowlists
- kept the v0.1 autonomous memory runtime behavior unchanged

## Recommended tested stack
- `openclaw >= 2026.3.12`
- `claw-memory-system = 0.1.2`
- `memory-lancedb-pro >= 1.1.0-beta.8`

Companion repository:
- https://github.com/CortexReach/memory-lancedb-pro

## Recommended install flow
```bash
openclaw plugins install memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
openclaw plugins install <claw-memory-system-github-url>
openclaw plugins enable claw-memory-system
```

Then bootstrap the runtime:
```text
Call claw_memory_bootstrap
```

If `memory-lancedb-pro` is not available from the default plugin source:
```bash
openclaw plugins install https://github.com/CortexReach/memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

## Notes
This release does not change the default runtime model:
- queue-only lifecycle capture remains default-off
- batch governance remains the recommended autonomous absorption path
- semantic recall still requires `memory-lancedb-pro` for full effectiveness
