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

## 完整功能的必要依赖
如果要获得完整语义召回能力，**必须同时安装并启用 `memory-lancedb-pro`**。

推荐测试组合（`v0.1.1`）：
- `openclaw >= 2026.3.12`
- `claw-memory-system = 0.1.1`
- `memory-lancedb-pro >= 1.1.0-beta.8`

推荐安装方式：
```bash
openclaw plugins install memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

如果当前环境的默认插件源里没有 `memory-lancedb-pro`，则应改用该插件的仓库地址安装后再启用：

```bash
openclaw plugins install https://github.com/CortexReach/memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

如果新环境里只有 `claw-memory-system`，没有 `memory-lancedb-pro`，本项目仍可提供：
- structured memory
- pending queue
- batch governance
- exact search

但**语义召回能力会明显下降**，整体效果会打折。

## 推荐使用流程
1. 先安装并启用 `memory-lancedb-pro`
2. 再安装并启用本插件
3. 如果当前 OpenClaw 环境使用显式 allowlist，请把两个插件都加入 `plugins.allow`
4. 运行 bootstrap
5. 构建 exact index（可选）
6. 启用 batch governance 定时任务
7. 如需生命周期自动捕获，再显式打开 `autoTurnCapture`

推荐 allowlist 示例：
```json
{
  "plugins": {
    "allow": [
      "memory-lancedb-pro",
      "claw-memory-system"
    ]
  }
}
```

## 关键文档
- `docs/quickstart-openclaw-chat-install.zh-CN.md`
- `docs/full-enable-guide.zh-CN.md`
- `docs/autonomous-memory-runtime.zh-CN.md`
- `docs/release-notes-v0.1.zh-CN.md`
- `docs/final-release-matrix.zh-CN.md`
- `docs/portable-release-checklist.zh-CN.md`
- `docs/lifecycle-integration-notes.zh-CN.md`

历史过程性方案文档已归档到 `docs/archive/plans/`，避免干扰首次接触本项目的人。
