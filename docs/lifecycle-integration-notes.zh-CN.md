# Lifecycle Integration Notes

## 结论
当前查到的 OpenClaw 插件 hook 名称中，**存在可用的后置生命周期面**：

- `llm_output`
- `agent_end`
- `message_sent`
- `tool_result_persist`

相比之下：
- `before_prompt_build`
- `before_agent_start`
是前置，不适合 queue-only turn capture

## event shape 确认
### `PluginHookAgentContext`
可用字段：
- `agentId`
- `sessionKey`
- `sessionId`
- `workspaceDir`
- `messageProvider`
- `trigger`
- `channelId`

### `PluginHookAgentEndEvent`
可用字段：
- `messages: unknown[]`
- `success: boolean`
- `error?: string`
- `durationMs?: number`

### `PluginHookLlmOutputEvent`
可用字段：
- `assistantTexts: string[]`
- `lastAssistant?: unknown`
- `usage?`

## Release-safe 选择
对于 autonomous memory v0.1，推荐优先使用：

### 首选：`agent_end`
优点：
- 最接近完整 turn 收尾
- `messages` 可用，利于提取 user / assistant 文本
- 不依赖 prompt 注入

### 备选：`llm_output`
优点：
- 有 assistantTexts
缺点：
- 不保证是完整 turn 收尾
- 没有完整 `messages`

### 不建议直接用：`message_sent`
原因：
- 更偏 delivery 语义
- 并非所有 surface / mode 都等价于 agent turn 完成

## v0.1 建议策略
- 默认关闭 `autoTurnCapture`
- 打开后优先挂到 `agent_end`
- 行为保持 queue-only
- 若 event payload 不足，再退回保守替代方案

## 下一步
1. 在 claw-memory-system 里做最小 `agent_end` wiring spike
2. 仅使用当前 run 的 messages 做 user/assistant 文本提取
3. 默认失败静默，不影响正常对话
