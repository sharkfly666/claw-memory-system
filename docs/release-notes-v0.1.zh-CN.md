# Release Notes v0.1.1

## 亮点
- 引入结构化记忆层：facts / preferences / tasks / episodes
- 引入 pending turn queue：`turn_candidates.json`
- 支持 queue-only 生命周期捕获（默认关闭）
- 支持 batch governance 自动吸收 safe drafts
- 支持 dedupe / merge / supersede / noop
- 支持 fresh workspace end-to-end smoke

## 默认行为
- 默认不开启自动 turn capture
- 即使开启，也默认只 queue，不直接写正式结构化层
- batch governance 默认启用，推荐每 6 小时跑一次
- classifier 需要通过 `turnCaptureMinConfidence` 才会入队
- 完整功能依赖 `memory-lancedb-pro` 作为语义召回层

## 已知限制
- post-turn classifier 当前为规则型，不是 LLM-powered semantic classifier
- lifecycle 自动接入当前采用 release-safe queue-only 路径
- MEMORY.md compact / 自动摘要还未接入默认自动化
- queue 的 dedupe 当前主要基于稳定 key / 文本标准化，不是深度语义近似去重

## 推荐使用方式
- 先启用 batch governance
- 先观察 queue 与 governance report
- 再决定是否打开 `autoTurnCapture`

## 不建议的用法
- 不要在 v0.1 就直接打开“turn 直写 structured memory”
- 不要把 supersede 策略设得过于激进
- 不要跳过 fresh workspace smoke 就对外发布
