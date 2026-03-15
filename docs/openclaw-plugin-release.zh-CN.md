# 发布 OpenClaw 插件

这份文档说明 `claw-memory-system` 在发布到 GitHub 之后，怎样才算是 OpenClaw 的标准安装路径。

## 一个关键区别

把仓库放到 GitHub 上，**不等于** OpenClaw 就能直接拿一个 GitHub 仓库 URL 来安装。

根据我在 2026 年 3 月 13 日本地核验的结果，`openclaw plugins install` 当前主要接受这些来源：

- 本地路径
- archive 文件
- npm package spec

所以，“只有一个 GitHub repo URL”**不应该默认视为标准安装路径**。

## 推荐的公开分发方式

标准公开分发，建议走下面一条或两条：

### 方案 A：发布到 npm

把插件包发布到 npm，然后让用户直接按 package spec 安装：

```bash
openclaw plugins install claw-memory-system@0.1.0
openclaw plugins enable claw-memory-system
```

如果你的目标是让终端用户不需要先 clone 仓库，这通常是最干净的路径。

### 方案 B：发布 GitHub Release archive

生成一个 release 归档，比如 `claw-memory-system-0.1.0.tgz` 或 `.zip`，用户下载后按本地归档安装：

```bash
openclaw plugins install /path/to/claw-memory-system-0.1.0.tgz
openclaw plugins enable claw-memory-system
```

如果你想先有一个稳定发布物，但暂时不想发 npm，这条路径更稳妥。

## 本地开发安装仍然有效

对于本地开发或源码体验，仍然可以直接这样装：

```bash
git clone <repo>
cd claw-memory-system
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
```

这依然是开发者最直接的路径，但它不等于“远程标准安装”。

## 当前仓库的打包状态

这个仓库现在已经具备 OpenClaw 插件包的基本结构：

- [`package.json`](../package.json)
- [`openclaw.plugin.json`](../openclaw.plugin.json)
- 插件入口 [`index.ts`](../index.ts)
- Python runtime 源码 [`src/claw_memory_system`](../src/claw_memory_system)
- bridge/runtime 脚本 [`scripts`](../scripts)

目前 npm 打包白名单已经收窄，只会带上运行所需的源码，不再把 Python 的 `__pycache__` 一起打进发布包。

## 发布前检查清单

发布前建议按这个顺序检查：

1. 同步更新 [`package.json`](../package.json) 和 [`openclaw.plugin.json`](../openclaw.plugin.json) 里的版本号。
2. 核对打包内容：

```bash
PATH=/Users/jiangjk/.nvm/versions/node/v22.16.0/bin:$PATH \
npm_config_cache=/tmp/claw-memory-system-npm-cache \
npm pack --dry-run --json
```

3. 跑仓库回归测试：

```bash
python3 -m unittest discover -s tests -v
```

4. 发布其中一种分发物：
- npm package：`claw-memory-system@<version>`
- archive 归档：`claw-memory-system-<version>.tgz` 或 `.zip`

5. 在真实宿主里验证安装：

```bash
openclaw plugins install <本地路径或 package spec>
openclaw plugins enable claw-memory-system
openclaw plugins info claw-memory-system
```

6. 跑一遍最小可用性检查：

```bash
openclaw memory-pro stats --scope agent:main --json
openclaw agent --session-id claw-memory-ready-check \
  --message "Call claw_memory_integration_check with skip_smoke=true. Return only compact JSON with ok, semantic_provider, vector_hits, and used_tools." \
  --json
```

## 安装后仍然要保持的架构

OpenClaw 的语义记忆 slot 仍然应该保留给 `memory-lancedb-pro`。

`claw-memory-system` 当前是一个 tool plugin bridge，它补的是：

- facts
- exact lookup
- migration tooling
- runtime diagnostics

## 面向最终用户的简化说法

后面你对外可以直接这么说：

- 如果已经把仓库 clone 到本地，就按本地路径安装。
- 如果要走标准远程安装，请提供 npm package 或 release archive。
- 不要默认假设 OpenClaw 能直接通过原始 GitHub 仓库 URL 安装。
