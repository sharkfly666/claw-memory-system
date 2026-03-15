# Release v0.1 Checklist

目标：第一个 release 就足够稳，不以“实验”心态发布。

## 必须完成
- [x] bootstrap 完整 runtime
- [x] facts / preferences / tasks / episodes / turn_candidates stores
- [x] governance report
- [x] candidate drafts
- [x] preview / merge / supersede / noop
- [x] batch governance
- [x] turn candidate queue
- [x] new workspace smoke
- [x] bridge tools: bootstrap / batch governance / classify / queue
- [x] cron automation path（至少示例已验证）

## Release safety defaults
- [x] autoTurnCapture 默认 false
- [x] autoTurnQueueOnly 默认 true
- [x] batchGovernanceEnabled 默认 true
- [x] direct structured auto-write 默认不启用
- [x] batch governance 只自动处理 safe drafts

## 发布前还要确认
- [ ] turn lifecycle 实际接入点确认（queue-only）
- [ ] lifecycle 接入 smoke
- [ ] docs 首页 / README 对 autonomous runtime 做清晰说明
- [ ] release note：说明默认行为、已知限制、推荐调度

## 已知限制（release notes 应明确）
- post-turn classifier 当前为规则型，不是 LLM judgment router
- lifecycle 真实自动接入尚未完成前，turn capture 仍需通过桥接/CLI/未来 hook wiring 触发
- MEMORY.md compact 尚未自动化
- queue 当前主要通过 exact dedupe key 处理，语义近似 dedupe 仍可继续增强
