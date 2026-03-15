# 集成 `memory-lancedb-pro`

这份文档说明如何在 OpenClaw 中同时使用 **`memory-lancedb-pro` + `claw-memory-system`**。

## 目标

采用职责分离的组合方式：

- **`memory-lancedb-pro`** 负责 semantic / hybrid recall
- **`claw-memory-system`** 负责 facts、exact search、migration、compatibility

这是当前最推荐的集成方式。

---

## 两套系统分别负责什么

### `memory-lancedb-pro`
适合负责：
- semantic recall
- hybrid vector + BM25 retrieval
- reranking
- 历史对话语义相似召回

### `claw-memory-system`
适合负责：
- current truth / structured facts
- exact search / page index
- human-readable memory organization
- legacy memory migration
- time-aware storage evolution

---

## 前置条件

你需要：
- 一个可用的 OpenClaw 安装
- 一个已配置的 OpenClaw workspace
- `memory-lancedb-pro` 已作为 OpenClaw 插件可用
- 本项目已在本地存在

---

## 第 1 步 —— 保留 `memory-lancedb-pro` 作为语义后端

在 OpenClaw 中，继续让 memory plugin slot 指向 `memory-lancedb-pro`。

概念上类似：

```json
{
  "plugins": {
    "slots": {
      "memory": "memory-lancedb-pro"
    }
  }
}
```

> 你实际的 OpenClaw 配置结构可能和这个示意不同，但核心原则不变：**现在不要替换掉 semantic memory slot**。

---

## 第 2 步 —— 安装 `claw-memory-system` 插件

推荐的标准路径：

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

这个插件负责暴露 facts / exact-search / bootstrap / diagnostic 工具，但它**不会**替换 `memory` slot。

---

## 第 3 步 —— 把 `claw-memory-system` runtime bootstrap 到 workspace

如果 repo 放在 workspace 之外，推荐这样做：

```bash
cd /path/to/claw-memory-system
./scripts/bootstrap-openclaw.sh ~/.openclaw/workspace
```

或者手动：

```bash
cd /path/to/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo /path/to/claw-memory-system
```

如果 repo 本身就是 clone 在 OpenClaw workspace 内，也同样支持：

```bash
cd ~/.openclaw/workspace/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/.openclaw/workspace/claw-memory-system
```

---

## 第 4 步 —— 构建精确搜索索引

```bash
cd ~/.openclaw/workspace
python3 memory-system/index/build_pageindex.py
```

它会建立：
- facts 索引
- `MEMORY.md` 索引
- `memory/*.md` 索引

---

## 第 5 步 —— 验证两层都正常工作

### 语义层（`memory-lancedb-pro`）
继续使用 OpenClaw 现有 memory recall 流程，确认 semantic recall 仍正常工作。

### exact / facts 层（`claw-memory-system`）

```bash
cd ~/.openclaw/workspace
python3 memory-system/facts/facts_cli.py list
python3 memory-system/index/search_pageindex.py "primary model"
```

---

## 推荐工作流

### 语义 / 模糊历史问题
继续使用由 `memory-lancedb-pro` 支撑的 OpenClaw 记忆流程。

### 当前真值 / 精确查询问题
使用 `claw-memory-system`：
- facts
- page index
- migration tools
- plugin bridge tools

### 存量迁移
使用：
- `scripts/run_memos_local_migration_preview.py`
- `scripts/run_memos_local_import.py`
- 详细说明见：`docs/memos-local-migration.zh-CN.md`

---

## 当前运行模型

```text
OpenClaw
  ├─ semantic recall -> memory-lancedb-pro
  ├─ facts           -> claw-memory-system
  ├─ exact search    -> claw-memory-system
  └─ text memory     -> MEMORY.md / daily memory
```

也就是说，这不是替换 OpenClaw 现有记忆，而是：

> **在现有语义记忆之上做增强。**

---

## 为什么当前推荐这种方式

因为到现在为止，它的平衡最好：
- 保留成熟的 semantic recall
- 增加可靠的 facts
- 增加 exact search
- 获得 migration / compatibility 结构
- 避免一次性替换带来的风险

---

## 后续演进方向

后面如果需要，可以继续往这些方向走：
- 自动 sidecar 同步
- vector adapter 抽象
- hybrid memory plugin integration

但就当前阶段来说，最推荐的答案仍然是：

> **保留 `memory-lancedb-pro` 作为语义层，再通过原生 tool plugin 叠加 `claw-memory-system` 作为 facts / exact-search / migration 层。**
