# Claw Memory System

本项目是一个面向 OpenClaw 的本地优先混合记忆系统。

## v0.1 自动记忆运行时亮点
- 结构化层：facts / preferences / tasks / episodes
- pending turn queue：`turn_candidates.json`
- post-turn classifier（规则型）
- queue-only autonomous lifecycle wiring（默认关闭）
- batch governance（可自动吸收 safe drafts）
- dedupe / merge / supersede / noop
- fresh workspace smoke 已通过

## 默认安全策略
- `autoTurnCapture = false`
- `autoTurnQueueOnly = true`
- `turnCaptureMinConfidence = 0.88`
- `batchGovernanceEnabled = true`
- `batchGovernanceEvery = 6h`

默认原则：
> 先入队，再治理，再吸收。

不会默认直接把每轮对话写进正式结构化层。

## 推荐使用流程
1. 安装并启用插件
2. 运行 bootstrap
3. 构建 exact index（可选）
4. 启用 batch governance 定时任务
5. 如需生命周期自动捕获，再显式打开 `autoTurnCapture`

## 关键文档
- `docs/quickstart-openclaw-chat-install.zh-CN.md`
- `docs/full-enable-guide.zh-CN.md`
- `docs/autonomous-memory-runtime.zh-CN.md`
- `docs/release-notes-v0.1.zh-CN.md`
- `docs/final-release-matrix.zh-CN.md`
- `docs/portable-release-checklist.zh-CN.md`
- `docs/lifecycle-integration-notes.zh-CN.md`

历史过程性方案文档已归档到 `docs/archive/plans/`，避免干扰首次接触本项目的人。
