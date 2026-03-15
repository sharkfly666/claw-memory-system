# Final Release Matrix

发布前最后检查矩阵。

## Runtime
- [x] bootstrap fresh workspace
- [x] turn queue capture
- [x] batch governance absorb
- [x] noop equivalence skip
- [x] dedupe on queue ingest
- [x] queue-only lifecycle wiring in plugin

## Smoke
- [x] autonomous memory smoke
- [x] lifecycle queue smoke
- [x] fresh workspace smoke

## Defaults
- [x] autoTurnCapture=false
- [x] autoTurnQueueOnly=true
- [x] turnCaptureMinConfidence=0.88
- [x] batchGovernanceEnabled=true
- [x] batchGovernanceEvery=6h

## Docs
- [x] README.md
- [x] README.zh-CN.md
- [x] autonomous-memory-runtime.zh-CN.md
- [x] autonomous-memory-runtime.md
- [x] release-notes-v0.1.zh-CN.md
- [x] portable-release-checklist.zh-CN.md
- [x] release-v0.1-checklist.zh-CN.md
- [x] lifecycle-integration-notes.zh-CN.md

## Known gaps
- classifier is still rule-based
- turn lifecycle wiring is release-safe queue-only, not direct structured write
- MEMORY.md compact remains future work
