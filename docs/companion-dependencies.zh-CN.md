# Companion Dependencies（配套依赖）

## memory-lancedb-pro
仓库地址：
- https://github.com/CortexReach/memory-lancedb-pro

在 `claw-memory-system v0.1.0` 中，`memory-lancedb-pro` 是当前唯一经过完整验证并官方推荐的 semantic recall companion plugin。

### 推荐安装方式
优先尝试：
```bash
openclaw plugins install memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

如果当前环境的默认插件源里没有该插件，则可改用仓库地址安装：
```bash
openclaw plugins install https://github.com/CortexReach/memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

### 推荐测试组合（v0.1.0）
- `openclaw >= 2026.2.0`
- `claw-memory-system = 0.1.0`
- `memory-lancedb-pro >= 1.1.0-beta.8`

### 缺少该依赖时的影响
如果未安装 `memory-lancedb-pro`，`claw-memory-system` 仍可提供：
- structured memory
- pending queue
- batch governance
- exact search

但语义召回能力会明显下降，整体体验会打折。
