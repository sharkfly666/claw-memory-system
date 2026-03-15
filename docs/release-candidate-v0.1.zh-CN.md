# Release Candidate v0.1

## 版本定位
这是 claw-memory-system 的第一个可发布候选版本，目标不是“最聪明”，而是：

- 默认安全
- 可移植
- 可审计
- fresh workspace 可跑通
- OpenClaw 日常使用可逐步自动化

## 已完成能力
- facts / preferences / tasks / episodes 结构化层
- pending turn queue (`turn_candidates.json`)
- queue-only lifecycle wiring (`agent_end`)
- batch governance 自动吸收 safe drafts
- dedupe / merge / supersede / noop
- autonomous memory smoke
- lifecycle queue smoke
- release-safe defaults

## 默认策略
- `autoTurnCapture = false`
- `autoTurnQueueOnly = true`
- `turnCaptureMinConfidence = 0.88`
- `batchGovernanceEnabled = true`
- `batchGovernanceEvery = 6h`

## 发布结论
按当前检查结果，v0.1 已经满足 release candidate 条件。

## 已知不纳入 v0.1 的内容
- LLM 驱动 classifier
- MEMORY.md 自动摘要/compact
- 深度语义近似 dedupe
- 直接 turn -> structured memory 自动写入

这些明确留到后续版本。

## 最终发布前确认
- [x] 全量测试通过
- [x] autonomous memory smoke 通过
- [x] lifecycle queue smoke 通过
- [x] final release matrix 已收口
- [x] release notes 已补充
