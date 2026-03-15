# Portable Release Checklist（可移植发布检查清单）

用于确保 claw-memory-system 不只是“在当前机器可用”，而是能给其他 OpenClaw 用户直接使用。

## 1. 运行时初始化
- [ ] `claw_memory_bootstrap` 能在空工作区创建完整 runtime
- [ ] `stores/v2/` 下所有 JSON store 都有默认值
- [ ] 新增 store 必须加入 bootstrap
- [ ] 新增 store 必须有兼容默认 schema_version

## 2. Bridge / CLI 入口
- [ ] 每个核心能力都能通过 bridge 调用
- [ ] CLI 入口不依赖私有 shell alias 或本地路径
- [ ] `PYTHONPATH` 由 bridge 正确注入

## 3. 自动运行安全性
- [ ] post-turn classifier 默认只判定或入队，不直接高风险写入
- [ ] batch governance 默认只 auto-apply safe drafts
- [ ] supersede 默认需要明确治理逻辑
- [ ] equivalence noop 默认开启

## 4. 可移植性约束
- [ ] 核心逻辑不写死特定用户路径
- [ ] 核心逻辑不写死特定业务语义
- [ ] 用户特定 bootstrap 数据与通用框架分离
- [ ] docs 中明确哪些是示例、哪些是通用能力

## 5. 文档
- [ ] Quick start
- [ ] Runtime architecture
- [ ] Store schema overview
- [ ] Default safety policy
- [ ] Recommended cron setup
- [ ] Troubleshooting（例如 PYTHONPATH / bridge 问题）

## 6. 测试
- [ ] 新 store 有单元测试
- [ ] 新 bridge/CLI 有最少 smoke 验证
- [ ] batch governance 覆盖 queue + noop + dedupe
- [ ] bootstrap 修改后全量测试通过

## 7. 建议的发布门槛
- 通过全量测试
- 在新 workspace 验证 bootstrap + batch governance + turn queue
- 文档完整后，再考虑接入真实 turn lifecycle
