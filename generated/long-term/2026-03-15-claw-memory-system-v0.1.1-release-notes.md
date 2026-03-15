# claw-memory-system v0.1.1

Patch release focused on installation clarity and companion dependency guidance.

## What changed
- clarified that full functionality depends on `memory-lancedb-pro`
- added recommended tested stack for v0.1.1
- added direct fallback install instructions using the `memory-lancedb-pro` GitHub repository
- updated README / README.zh-CN / quickstart / full-enable docs
- kept the v0.1 autonomous memory runtime behavior unchanged

## Recommended tested stack
- `openclaw >= 2026.2.0`
- `claw-memory-system = 0.1.1`
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
