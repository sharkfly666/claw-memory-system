# 安装到 OpenClaw

现在优先推荐使用插件安装。

如果你想继续使用旧的“直接 bootstrap”方式，下面也保留了兼容说明。

本项目采用 **代码 / 数据分离** 的设计：

- **代码仓库** 可以放在任意目录（例如从 GitHub clone 下来）
- **运行实例数据** 放在 OpenClaw workspace 下的 `memory-system/`

这样可以避免把生成数据、索引和源码混在一起。

## 推荐目录结构

```text
~/.openclaw/workspace/
├── memory-system/           # 数据实例
│   ├── code -> /path/to/claw-memory-system
│   ├── facts/
│   ├── index/
│   ├── migrations/
│   └── receipts/
└── ... 其他 workspace 文件

/path/to/claw-memory-system/ # clone 下来的仓库或插件源码
```

## 推荐路径：作为原生插件安装

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

安装后先 bootstrap 一次 runtime：

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_bootstrap \
  --workspace ~/.openclaw/workspace
```

然后再继续执行：

```bash
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_build_index \
  --workspace ~/.openclaw/workspace

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_search_index \
  --workspace ~/.openclaw/workspace \
  --query "primary model"
```

## 直接 bootstrap 路径：repo 克隆在 workspace 外部

```bash
git clone https://github.com/<you>/claw-memory-system.git ~/dev/project/github/claw-memory-system
cd ~/dev/project/github/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/dev/project/github/claw-memory-system
```

## 直接 bootstrap 路径：repo 直接克隆在 OpenClaw workspace 内

如果用户把仓库直接 clone 到 OpenClaw workspace，比如：

```text
~/.openclaw/workspace/claw-memory-system
```

也是支持的。执行：

```bash
cd ~/.openclaw/workspace/claw-memory-system
PYTHONPATH=src python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo ~/.openclaw/workspace/claw-memory-system
```

这样依然会生成单独的运行数据目录：

```text
~/.openclaw/workspace/memory-system
```

所以即便 repo 本身位于 workspace 内，**代码和运行数据在逻辑上仍然是分离的**。

## bootstrap 后如何使用

通过 workspace 中的 wrapper 入口来用：

```bash
cd ~/.openclaw/workspace
python3 memory-system/index/build_pageindex.py
python3 memory-system/index/search_pageindex.py "primary model"
python3 memory-system/facts/facts_cli.py list
```

## 说明

- 当前向量召回层仍建议由外部系统提供（例如 `memory-lancedb-pro`）
- 本项目当前主要提供：facts / exact search / migration tooling / compatibility 结构
- 新增的插件包是 tool bridge，不替换 semantic memory slot
- 插件优先安装细节可见：`docs/openclaw-plugin-install.zh-CN.md`
