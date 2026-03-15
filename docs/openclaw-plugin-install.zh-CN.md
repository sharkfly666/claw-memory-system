# 以 OpenClaw 原生插件方式安装

`claw-memory-system` 现在已经支持原生 OpenClaw 插件包。

如果你的目标是让 OpenClaw 通过插件系统发现、安装和使用本项目，这就是**当前推荐的标准路径**。

## 这个插件负责什么

这个插件当前是一个 **tool bridge**，不是 memory backend 替换品。

它把仓库内部已经存在的能力通过插件工具暴露出来，包括：

- workspace bootstrap
- exact-search 索引构建
- exact-search 查询
- facts list / get
- integration check
- deep local integration + migration check

它**不会**接管 OpenClaw 的 `memory` slot。

## 继续保留语义记忆后端

请继续让 `memory-lancedb-pro` 作为语义记忆后端：

```json
{
  "plugins": {
    "slots": {
      "memory": "memory-lancedb-pro"
    }
  }
}
```

`claw-memory-system` 负责 facts、exact lookup、migration 和诊断链路。

## 从本地路径安装

在仓库根目录执行：

```bash
cd /path/to/claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

如果你的 OpenClaw 版本在安装时已经自动启用了插件，额外执行一次 `enable` 也没有副作用。

## 如果 install 报 allowlist 错误

在我本地于 2026 年 3 月 13 日验证的 OpenClaw 版本上，`install` 有可能已经把插件复制进 `~/.openclaw/extensions/`，但在同一个命令的 allowlist 更新阶段报错。

如果遇到这种情况，继续执行：

```bash
openclaw plugins info claw-memory-system
openclaw plugins enable claw-memory-system
```

只要 `info` 已经能看到 `~/.openclaw/extensions/claw-memory-system` 这个来源，就说明复制已经成功，接下来补一条 `enable` 就能完成激活。

## bootstrap 一次 workspace 运行实例

插件安装完成后，先初始化一次 workspace 内的运行数据目录：

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_bootstrap \
  --workspace ~/.openclaw/workspace
```

这样会在 workspace 下创建 `memory-system/` 运行目录。

默认情况下，插件还会在 gateway 启动时自动 bootstrap workspace，并拉起本地管理后台 HTTP 进程。控制台入口是：

```text
http://127.0.0.1:18789/plugins/claw-memory-system
```

如果你是在 gateway 已经运行的情况下，才刚把新的插件代码同步到 `~/.openclaw/extensions/claw-memory-system`，要再执行一次：

```bash
openclaw gateway restart
```

这样宿主才会吃到新的 service / route 注册逻辑。除非你显式把 `autoStartAdmin` 配成 `false`，否则不需要手动启动管理后台。需要自定义时，再覆盖 `adminHost`、`adminPort`、`autoStartAdmin`。

## 生产可用最小检查清单

如果你要判断“现在是否已经可以正常用 OpenClaw”，先跑这三条：

```bash
openclaw plugins info claw-memory-system
openclaw memory-pro stats --scope agent:main --json
openclaw agent --session-id claw-memory-ready-check \
  --message "Call claw_memory_integration_check with skip_smoke=true. Return only compact JSON with ok, semantic_provider, vector_hits, and used_tools." \
  --json
```

满足下面这些条件，就可以把当前环境视为可直接使用：

- `claw-memory-system` 显示 `Status: loaded`
- `memory-lancedb-pro` 仍然是 `plugins.slots.memory` 的目标
- `openclaw memory-pro stats` 能正常返回统计结果
- agent 回合返回 `"ok": true`，并且 `"semantic_provider": "memory-lancedb-pro"`

通常情况下，`claw-memory-system` 不需要额外配置。只有在你需要覆盖 `pythonBin`、`repoPath`、`workspaceDir`、`openclawHome` 或 `openclawBin` 时，才需要补 `plugins.entries.claw-memory-system.config`。

如果你在本地路径安装后继续修改 repo，要注意 OpenClaw 实际执行的是 `~/.openclaw/extensions/claw-memory-system` 里的拷贝。要让宿主吃到新代码，需要重装插件或同步这份副本。

## 常用后续命令

```bash
cd /path/to/claw-memory-system
python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_build_index \
  --workspace ~/.openclaw/workspace

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_search_index \
  --workspace ~/.openclaw/workspace \
  --query "primary model"

python3 -m claw_memory_system.openclaw_plugin_bridge \
  claw_memory_facts_list \
  --workspace ~/.openclaw/workspace
```

## OpenClaw 现在能直接安装什么

我本地看到的 `openclaw plugins install --help` 说明，当前直接接受的来源主要是：

- 本地路径
- archive 文件
- npm package spec

这意味着“只给一个 GitHub 仓库 URL”**不能默认假设一定能直接安装**。

如果你希望远程标准安装，建议把仓库打包成：

- npm package
- `.zip` / `.tgz` / `.tar.gz` 归档

## 兼容保留：旧的 bootstrap 路径

不通过插件系统、直接 bootstrap 到 workspace 的老路径仍然可用：

```bash
./scripts/bootstrap-openclaw.sh ~/.openclaw/workspace
```

如果你只是本地开发仓库、暂时不需要 OpenClaw 的原生插件发现能力，这条路径仍然适合。

## 可选的更深验收

仓库里还提供了：

```bash
python3 scripts/run_openclaw_integration.py --workspace ~/.openclaw/workspace
```

这条命令会包含 Beta 浏览器 smoke 路径。如果你当前 Python 环境没有 `playwright`，这一步会失败，但并不代表宿主安装不可用。此时日常判断是否可用，以上面的最小检查清单为准。
