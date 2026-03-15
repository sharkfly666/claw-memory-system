# Claw Memory System 现有记忆去重 / 分层整理方案

这份方案专门针对当前 OpenClaw 工作区的现实情况，不空谈。

目标：
- 减少重复
- 明确主层
- 清理冲突
- 把真正有价值的记忆迁到结构化层

---

## 一、当前现状

当前你这边的主要问题不是“没有记忆”，而是：

1. **重要事实主要在 memory tool 和 MEMORY.md 中**
2. **preferences/tasks/episodes 结构化层几乎是空的**
3. **daily memory 里混有配置、过程、结论、临时日志**
4. **同一主题有多条近义记忆并存**

所以整理的目标，不是删很多，而是：

> **把主记录扶正，把历史记录降级。**

---

## 二、整理原则

### 原则 1：不直接粗暴删除
先迁移、标记、归档，再考虑 forget。

### 原则 2：每个主题只留一个“当前真相主记录”
例如：
- PanSou 镜像优先级
- 早报发送时间
- QClaw 路径禁用

这些都应该只有一个主记录。

### 原则 3：历史过程不要和当前真相抢位置
- 当前值 → fact / preference / active task
- 历史原因 → episode

### 原则 4：daily memory 是原料，不是主仓
原料可以保留，但高价值内容应该上浮。

---

## 三、按主题的整理方案

## 主题 A：PanSou

### 当前看到的问题
- token 信息在 memory tool / MEMORY.md / token 文件里都有影子
- 镜像优先级存在旧版 preference 和记忆更新痕迹
- 新旧镜像顺序并存

### 目标分层

#### facts
- `pansou.token_file`
- `pansou.oauth_url`
- `pansou.authenticated_service`
- `pansou.mirror_priority`

#### preferences
- `user.pansou_search_preference`
  - 优先 Quark
  - 优先最新
  - 先验链接有效性

#### episodes
- `episode.pansou-mirror-migration-2026-03`
  - 从 wenyuanw 切换到 daiyazhi
  - 新增第 4 镜像
  - 为什么做这个调整

### 处理动作
1. 更新/合并 `pansou.mirror_priority` 为唯一主记录
2. 把“搜索偏好”单独抽成 preference
3. 把镜像演化过程落成一条 episode
4. 旧近义记忆标记 superseded 或后续 forget

---

## 主题 B：每日早报

### 当前看到的问题
- 8:00 发送是明确事实
- 数据获取方式有多条记忆
- 还有失败/超时/Feishu 审核等历史过程
- memory 目录里有大量 daily-briefing 相关 markdown

### 目标分层

#### facts
- `daily_briefing.schedule`
- `daily_briefing.delivery_channel`
- `daily_briefing.weather_source`
- `daily_briefing.market_source`
- `daily_briefing.hot_topics_source`

#### tasks
- `task.daily-briefing-stability`
  - 当前是否还在优化
  - 阻塞点
  - 下一步

#### episodes
- `episode.daily-briefing-timeout-fix-2026-03`
- `episode.daily-briefing-feishu-safety-2026-03`
- `episode.daily-briefing-market-source-switch-2026-03`

#### MEMORY.md
- 只保留：发送时间、内容组成、状态摘要、已知问题

### 处理动作
1. 抽取 5~6 条明确 facts
2. 只保留 1 个 active task
3. 把历史修复过程从杂乱 memory 文本提炼成 2~3 条 episode
4. MEMORY.md 保持摘要化，不再承载细碎演化

---

## 主题 C：用户偏好 / 协作偏好

### 当前看到的问题
- 一部分在 USER.md / SOUL.md
- 一部分在 memory tool preference
- 一部分根本没结构化

### 目标分层

#### preferences
- `user.communication_style`
- `user.github_download_preference`
- `user.storage_lifecycle_preference`
- `agent.forbidden_qclaw_paths`

#### MEMORY.md / USER.md
- 保留人能快速读懂的摘要
- 但主规则应逐步有结构化镜像

### 处理动作
1. 把“直接高效、少废话”正式落成 preference
2. 把现有 preference 去重
3. USER.md 继续保留自然语言版本
4. 后续检索优先从 preference 层命中

---

## 主题 D：记忆系统自身配置与决策

### 当前看到的问题
- minScore / autoRecall / Gateway 重启这些信息大多散落在 other/agent:main
- 这类内容既有当前事实，也有历史决策

### 目标分层

#### facts
- 当前生效的 `memory.min_score`（如果能稳定确认）
- 当前 `autoRecall` 是否开启

#### tasks
- `task.claw-memory-layering`
- `task.memory-retrieval-quality`

#### episodes
- `episode.disable-autorecall-2026-03`
- `episode.minscore-adjustment-2026-03`
- `episode.gateway-restart-needed-after-config-2026-03`

### 处理动作
1. 当前真相进 fact
2. 演化原因进 episode
3. 后续优化工作进 task

---

## 四、具体整理顺序（推荐）

## Step 1：先不删，只盘点
输出一个主题清单：
- PanSou
- daily-briefing
- user preferences
- memory system config
- workspace/runtime facts

## Step 2：为每个主题指定主层
例如：
- PanSou 镜像优先级 → fact
- GitHub 下载偏好 → preference
- daily-briefing 稳定性 → task
- autoRecall 关闭原因 → episode

## Step 3：把结构化层补起来
优先补：
- preferences
- tasks
- episodes

因为 facts 现在已经有一部分了，但其余层基本空着。

## Step 4：对旧记录做状态处理
- active：当前有效
- superseded：被新记录替代
- archived：保留历史，不再默认召回

## Step 5：最后才考虑 forget
删掉那些：
- 明显重复且无独特历史价值的旧记忆
- 已被结构化且在其他层可查的噪声记录

---

## 五、建议新增的治理输出

建议后续生成一个类似这样的文件：

`memory-system/reports/memory-governance-report.json`

包含：
- 主题总览
- 主层映射
- 冲突记录
- 待迁移候选
- 待归档旧记录
- 建议 forget 列表

这会让整理工作不是一次性手工体力活，而是可持续治理。

---

## 六、你当前最值得先做的一轮整理

### 第一批优先主题
1. PanSou
2. daily-briefing
3. 用户协作偏好
4. 记忆系统自身配置

### 第一批优先动作
1. 正式建立 4~6 条 preference
2. 建 3~5 个 active/done task
3. 建 4~8 条关键 episode
4. 合并 2~4 条冲突 facts

这轮做完，整个系统的可用性会直接上一个台阶。

---

## 最后一句

去重整理不是为了“少”，而是为了做到：

**同一个问题来时，系统知道先信哪条。**
