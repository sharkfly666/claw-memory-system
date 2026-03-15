# OpenClaw 无人干预记忆自动运行方案

目标：让 claw-memory-system 在 OpenClaw 日常使用中自动运作，尽量减少人工干预。

## 一、自动运行的三条回路

### 回路 1：每轮结束后的自动记忆分类
- 输入：当前 turn 的 user / assistant / tool 结果
- 输出：是否写入 fact / preference / task / episode / daily memory
- 策略：
  - 高置信度：直接结构化写入
  - 中置信度：进入 candidate drafts
  - 低置信度：忽略

### 回路 2：定时 batch governance
- 生成 candidate drafts
- preview 冲突
- auto apply safe drafts
- refresh graph
- 写 governance report / batch report

### 回路 3：定时 compact
- 清理低质量候选
- supersede 旧记录
- 归档老 task
- 更新 MEMORY.md 摘要

## 二、在 OpenClaw 中的落点

### A. 插件 hook
优先考虑通过 plugin `api.on(...)` 接入 turn 生命周期，做 post-turn memory classifier。

### B. 定时任务
通过 OpenClaw cron 或插件内服务定时触发 batch governance / compact。

### C. 控制台
继续使用 web 控制台做可视化审计，但不依赖它触发日常自动运行。

## 三、建议实现顺序
1. 新增 post-turn memory classifier（最关键）
2. 暴露 batch governance 为 bridge tool / HTTP API
3. 用 cron 自动跑 batch governance
4. 再补 compact / MEMORY.md 自动摘要

## 四、当前代码状态
已完成：
- governance report
- drafts
- preview/apply/supersede
- merge + record quality
- batch governance workflow

待实现：
- post-turn classifier
- bridge tool 暴露 batch governance
- cron wiring
- MEMORY.md compact

## 五、原则
- 自动化不是全自动乱写
- 高置信度才直接落结构化层
- 中置信度先进候选队列
- 定时治理比每轮重治理更稳
