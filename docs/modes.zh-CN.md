# 记忆模式

当本项目与 OpenClaw 配合使用时，当前可以分成两种实际可落地的运行模式。

---

## 方案 1 —— Full mode（推荐）

使用：
- **`memory-lancedb-pro`** 负责语义召回
- **`claw-memory-system`** 负责 facts、exact search、migration、compatibility

### 你会得到
- semantic recall
- hybrid retrieval
- reranking
- structured facts
- exact search / page index
- human-readable memory organization
- migration and compatibility framework
- 更好的 time-aware memory 演进基础

### 适合谁
- 大多数 OpenClaw 用户
- 已经依赖长期语义记忆的用户
- 想平滑升级而不是硬切换的用户

### 职责划分

#### `memory-lancedb-pro`
负责：
- vector / semantic recall
- BM25 hybrid retrieval
- reranking
- conversation/history similarity search

#### `claw-memory-system`
负责：
- facts / current truth
- exact search
- migration tooling
- compatibility layer
- human-readable memory structure
- time-awareness design

### 为什么推荐它作为默认方案
因为就现阶段来说，它的平衡最好：
- 已有成熟语义召回能力
- 当前真值更稳定
- 精确查询更强
- 迁移可以渐进进行

---

## 方案 2 —— Minimal mode

使用：
- **只使用 `claw-memory-system`**
- 不使用 `memory-lancedb-pro`

### 你会得到
- structured facts
- exact search / page index
- human-readable memory
- migration and compatibility tools

### 你不会得到
- 成熟的 semantic recall
- conversation similarity search
- `memory-lancedb-pro` 提供的 hybrid vector + BM25 recall
- 高质量模糊历史召回能力

### 适合谁
- 想先要一个最简单、最可控方案的用户
- 主要需求是当前真值 + 精确查询的用户
- 可以接受后续再补向量后端的用户

### 代价
这个模式更纯、更简单，但在历史语义召回上会弱很多。

---

## 那要不要不用 `memory-lancedb-pro`？

### 简短回答
可以。

### 推荐回答
当前不建议把它作为默认方案。

如果用户不使用 `memory-lancedb-pro`，要明确知道：
`claw-memory-system` 目前 **并不能单独替代完整的 semantic memory backend**。

所以当前推荐是：

- **默认方案**：`memory-lancedb-pro + claw-memory-system`
- **轻量可选方案**：`claw-memory-system only`

---

## 配置指导

### Full mode
保留 OpenClaw 现有的语义记忆后端（例如 `memory-lancedb-pro`），再把 `claw-memory-system` bootstrap 到 workspace 中，用于：
- facts
- exact search
- migration
- compatibility

### Minimal mode
只 bootstrap `claw-memory-system`，依赖：
- facts
- page index
- text memory

但要预期：在接入其他向量后端之前，semantic recall 能力会偏弱。

---

## 产品方向建议

长期来看，应该把语义记忆理解成：

- 可插拔的 semantic backend
- facts / exact search / compatibility 独立演进
- 后续通过 vector adapter 接口接入不同实现

未来可能支持的后端：
- `memory-lancedb-pro`
- `sqlite-vec`
- local embedding backend
- 自研 hybrid backend

所以这个项目更合适的表述方式应该是：

> **Choose your semantic memory backend**

而不是：

> **Do I have to use `memory-lancedb-pro` forever?**
