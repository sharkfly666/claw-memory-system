# Claw Memory System

Local-first hybrid memory system for OpenClaw.

## v0.1 autonomous memory runtime
- Structured layers: facts / preferences / tasks / episodes
- Pending turn queue: `turn_candidates.json`
- Rule-based post-turn classifier
- Queue-only autonomous lifecycle wiring (default off)
- Batch governance that can absorb safe drafts automatically
- Dedupe / merge / supersede / noop
- Fresh-workspace smoke path passes

## Safe defaults
- `autoTurnCapture = false`
- `autoTurnQueueOnly = true`
- `turnCaptureMinConfidence = 0.88`
- `batchGovernanceEnabled = true`
- `batchGovernanceEvery = 6h`

Default principle:

> queue first, govern second, absorb third.

The system does **not** directly write every captured turn into structured memory by default.

## Recommended flow
1. Install and enable the plugin
2. Run bootstrap
3. Build the exact index (optional)
4. Enable or keep the batch governance cron
5. Only enable lifecycle auto capture explicitly when you want queue-only capture

## Key docs
- `docs/autonomous-memory-runtime.zh-CN.md`
- `docs/portable-release-checklist.zh-CN.md`
- `docs/lifecycle-integration-notes.zh-CN.md`
- `docs/release-v0.1-checklist.zh-CN.md`
