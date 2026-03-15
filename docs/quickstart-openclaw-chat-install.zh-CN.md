# OpenClaw Chat 安装快速指南

适用场景：用户在 OpenClaw chat 中直接提供本仓库的 GitHub 地址，希望 OpenClaw 下载后即可完成安装与基础启用。

## 目标
安装完成后，系统应具备：
- 插件已启用
- runtime 已 bootstrap
- batch governance 可运行
- 可选择开启 queue-only lifecycle capture

## 一、推荐安装步骤

### 1. 先安装语义记忆依赖 `memory-lancedb-pro`
为获得完整记忆效果，先安装并启用：

```bash
openclaw plugins install memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

如果当前环境的默认插件源里没有该插件，则改用其仓库地址安装后再启用：

```bash
openclaw plugins install https://github.com/CortexReach/memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

### 2. 安装本插件
在 OpenClaw chat 中，或终端中执行：

```bash
openclaw plugins install <github-repo-url>
openclaw plugins enable claw-memory-system
```

本地开发仓库也可：

```bash
openclaw plugins install "$(pwd)"
openclaw plugins enable claw-memory-system
```

### 2. 保持 semantic memory slot
本插件**不替代** `memory-lancedb-pro`。

推荐保留：
- `memory-lancedb-pro` 负责 semantic recall
- `claw-memory-system` 负责 structured memory / queue / governance / exact search

### 3. bootstrap runtime
推荐在 chat 中调用：

```text
Call claw_memory_bootstrap
```

或终端中执行：

```bash
python3 -m claw_memory_system.bootstrap_openclaw_instance \
  --workspace ~/.openclaw/workspace \
  --repo <repo-path>
```

这会创建：
- `memory-system/facts/`
- `memory-system/index/`
- `memory-system/stores/v2/`
- `turn_candidates.json`
- reports 目录等

### 4. 构建 exact index（可选）
```text
Call claw_memory_build_index
```

### 5. 启用 batch governance
推荐保留默认定时治理，或显式添加 cron：

```bash
openclaw cron add \
  --name claw-memory-batch-governance \
  --every 6h \
  --session isolated \
  --message "Call claw_memory_batch_governance with workspace=~/.openclaw/workspace. Return only a compact JSON summary." \
  --timeout-seconds 180
```

## 二、推荐默认配置

在 `openclaw.json` 中，推荐：

```json
{
  "plugins": {
    "entries": {
      "claw-memory-system": {
        "enabled": true,
        "config": {
          "autoStartAdmin": true,
          "autoTurnCapture": false,
          "autoTurnQueueOnly": true,
          "turnCaptureMinConfidence": 0.88,
          "batchGovernanceEnabled": true,
          "batchGovernanceEvery": "6h"
        }
      }
    }
  }
}
```

## 三、如何验证安装成功

### 最低验证
1. 插件已加载
2. `claw_memory_bootstrap` 能运行
3. `claw_memory_batch_governance` 能运行
4. `run_autonomous_memory_smoke.py` 通过（开发者场景）

### 推荐验证
- governance report 已生成
- batch report 已生成
- `turn_candidates.json` 已存在

## 四、默认安全说明
- 默认不开启自动 turn capture
- 即使开启，也默认 queue-only
- 默认不会直接把每轮对话写进正式 structured memory

## 五、推荐给新用户的启用顺序
1. 安装并启用插件
2. bootstrap runtime
3. 先观察 batch governance
4. 确认无误后，再显式开启 `autoTurnCapture`
