# Full Enable Guide（完整功能启用指南）

这份文档说明如何把 claw-memory-system 启用到 v0.1 所支持的**最完整、最推荐**状态。

## 一、v0.1 的“完整功能”定义
完整功能并不等于“激进自动写入”。

对于 v0.1，推荐的 full enable 状态是：
- `memory-lancedb-pro` 已安装并启用
- plugin enabled
- runtime bootstrapped
- semantic memory 继续由 `memory-lancedb-pro` 提供
- batch governance 自动运行
- lifecycle auto capture 开启
- lifecycle 仍然 **queue-only**
- structured memory 通过 governance 吸收，不直接 turn->write

## 二、推荐配置

```json
{
  "plugins": {
    "entries": {
      "claw-memory-system": {
        "enabled": true,
        "config": {
          "autoStartAdmin": true,
          "autoTurnCapture": true,
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

## 三、为什么 full enable 仍然 queue-only
因为 v0.1 的发布原则是：

> queue first, govern second, absorb third.

这能保证：
- 自动化存在
- 误写风险可控
- 治理报告可审计
- 行为对新用户更可预测

## 四、推荐配套动作
### 1. 确认 `memory-lancedb-pro` 已安装并启用
优先尝试：
```bash
openclaw plugins install memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```
如果默认插件源没有该插件，则改用其仓库地址安装：

```bash
openclaw plugins install https://github.com/CortexReach/memory-lancedb-pro
openclaw plugins enable memory-lancedb-pro
```

### 2. 启用 batch governance cron
建议每 6 小时一次。

### 3. 保留 governance report / batch report
这样才能审计自动吸收的结果。

### 4. 不要关闭 semantic memory
`memory-lancedb-pro` 继续提供语义召回。

## 五、如何判断“100% 功能已启用”
满足以下条件即可视为 v0.1 full enable：
- `autoTurnCapture = true`
- `autoTurnQueueOnly = true`
- batch governance 正常运行
- turn candidates 能入队
- batch governance 能消费 queue
- governance report / batch report 正常输出

## 六、不建议的配置
### 不建议：
- turn capture 直接写 structured memory
- 关闭 batch governance 但开启 auto turn capture
- 降低 `turnCaptureMinConfidence` 到过低值

## 七、v0.1 边界
v0.1 的 full enable 不是：
- 全自动无审计直写
- LLM 智能总结 MEMORY.md
- 深度语义 dedupe

这些都明确留给后续版本。
