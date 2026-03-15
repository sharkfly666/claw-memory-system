# 向量后端

## 当前推荐默认方案

当本项目与 OpenClaw 配合使用时，当前推荐把 **`memory-lancedb-pro`** 作为默认的语义召回层。

## 为什么推荐 `memory-lancedb-pro`

它已经为 OpenClaw 提供了比较成熟的语义记忆基础：

- 向量检索
- BM25 混合召回
- rerank 支持
- scope 隔离
- 很适合对话历史 / 上下文延续类召回

## 职责划分

### `memory-lancedb-pro`
负责：
- 语义召回
- hybrid retrieval
- reranking
- 长期对话记忆搜索

### `claw-memory-system`
负责：
- structured facts
- exact search / page index
- migration tooling
- human-readable memory organization
- time awareness
- compatibility and storage evolution
- routing / orchestration 设计

## 设计原则

当前项目 **不会** 直接把 `memory-lancedb-pro` 的源码合并进来。

而是把它视为一个外部语义层。

这样做的好处是边界更清晰：
- 向量记忆仍保持专门化
- facts 与 exact search 可以独立演进
- OpenClaw 集成可以渐进推进

## 当前集成模型

```text
OpenClaw
  ├─ semantic recall -> memory-lancedb-pro
  ├─ exact search    -> claw-memory-system / pageindex
  ├─ facts           -> claw-memory-system / facts
  └─ text memory     -> MEMORY.md / daily memory
```

## 适配器现状

当前仓库已经把默认运行时的语义适配路径补上了：

- `models.json` 中新增 `memory` profile 分类
- 支持 active profile 选择语义 provider
- 内置 `MemoryLanceDBProAdapter`
- `AdminAPI.from_workspace()` 与 `SearchRouter` 默认可以注入 vector 查询

内置适配器默认围绕 `memory-lancedb-pro` 的 CLI 入口工作：

```bash
openclaw memory-pro search "query" --json
```

如果需要，也可以在 profile 里显式覆盖命令，但仍沿用同一套 adapter contract。

示例 profile：

```json
{
  "name": "default",
  "provider": "memory-lancedb-pro",
  "enabled": true,
  "active": true,
  "limit": 10,
  "command": [
    "openclaw",
    "memory-pro",
    "search",
    "{query}",
    "--json",
    "--limit",
    "{limit}"
  ]
}
```

## 后续方向

下一步比较合理的是：
- 在同一 adapter registry 下继续补更多生产可用 provider
- 统一不同 provider 的 score / metadata 归一化
- 等 routing 稳定后，再考虑 hybrid plugin integration
