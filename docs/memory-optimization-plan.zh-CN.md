# Claw Memory System 当前记忆方案优化设计图

这份设计图只做三件事：

1. 明确当前方案的真实短板
2. 给出可落地的结构改造方向
3. 尽量沿用现有 claw-memory-system 架构，不推倒重来

---

## 一、当前方案诊断

当前实际是 **五层混合**：

1. OpenClaw `memory_*` 工具（向量/混合召回）
2. `memory-system/facts/facts.json`
3. `memory-system/stores/v2/preferences|tasks|episodes|sessions|graph`
4. `MEMORY.md`
5. `memory/YYYY-MM-DD.md`

架构本身不差，问题主要有四个：

### 问题 A：结构化层存在，但几乎没被日常工作流真正用起来
当前工作区里：
- `preferences.json` 还是空
- `tasks.json` 还是空
- `episodes.json` 还是空

也就是说，系统已经有“器官”，但还没开始供血。

### 问题 B：很多应该结构化的内容还停留在向量记忆或 markdown 文本中
比如：
- 用户沟通偏好
- PanSou 搜索偏好
- 进行中的长期任务
- 关键决策过程

结果就是：
- facts 偏少
- preference/task/episode 召回能力没被训练出来
- 向量层承担了不该承担的主账本职责

### 问题 C：同主题信息容易重复、过期、冲突
典型例子：
- PanSou 镜像优先级改过多次
- 早报数据源和投递规则发生过演化
- autoRecall/minScore 的历史决策与当前配置并存

### 问题 D：缺少“治理层”
目前能存、能搜、能改，但还缺：
- 哪类信息该落哪层
- 哪些记录可能冲突
- 哪些 active 记录应该归档
- 哪些 daily memory 候选值得提升为结构化记录

---

## 二、目标架构

## 目标 1：让每类信息有稳定主层

### 主层分工
- **facts**：当前真相 / 当前配置 / 可精确引用事实
- **preferences**：长期偏好 / 协作习惯 / 风格约束
- **tasks**：进行中的工作对象 / 状态机
- **episodes**：关键事件 / 决策过程 / 经验沉淀
- **MEMORY.md**：长期摘要 / 人类可读总览
- **daily memory**：原始流水 / 待提炼素材
- **semantic memory**：辅助召回，不做主账本

### 核心原则
> 先决定主层，再决定是否需要其他层的摘要映射。

不是每条信息都要全层落一遍。

---

## 目标 2：把“更新”变成一等公民

当前最值钱的能力不是 store，而是 **upsert + supersede + history**。

### 建议增强

#### facts
- 已有 history append，保留
- 增加“同主题冲突检查”报告

#### preferences
建议补：
- `status`: active / superseded / archived
- `superseded_by`
- `scope`
- `importance`
- `evidence`
- `summary`

#### tasks
建议补：
- `priority`
- `owner_scope`
- `outcome`
- `closed_at`
- `superseded_by`

#### episodes
建议补：
- `episode_type`
- `decision`
- `impact`
- `related_fact_keys`
- `related_preference_keys`
- `related_task_ids`

---

## 目标 3：加入治理与提炼流程

### 新增治理流程（推荐）

#### Flow A：daily memory -> migration candidates
从 daily memory 中提取候选项，分类为：
- fact candidate
- preference candidate
- task candidate
- episode candidate

#### Flow B：conflict detection
扫描结构化层，识别：
- 同主题多条 active preference
- 任务长期 active 但 `last_active_at` 过旧
- facts 与 preferences 对同一主题定义不一致
- MEMORY.md 摘要与 facts 主记录不一致

#### Flow C：weekly compact
每周进行一次：
- 归档 done/过旧 task
- 把高价值 episode 提炼进 MEMORY.md
- 删除或 supersede 明显陈旧 preference
- 重建 graph

---

## 三、建议的产品/代码改造点

## 改造点 1：新增 `memory governance report`

建议新增一个报告产物，例如：

`memory-system/reports/memory-governance-report.json`

至少包含：
- 结构化层记录数量统计
- 空层告警（如 preferences/tasks/episodes 为空）
- 冲突项列表
- 过旧 active task 列表
- 缺少 `summary/aliases/tags` 的低质量记录
- 值得提炼的 migration candidate 数量

这玩意很实用。没有治理报告，后面一定越存越乱。

---

## 改造点 2：新增“记忆分层建议器”

输入一条候选记忆，输出：
- 推荐层：fact / preference / task / episode / file-only
- 理由
- 推荐 key/id
- 推荐字段模板

这可以先做成：
- Python CLI
- 或 admin API endpoint
- 或 webapp 面板

这是把规范变成工具，而不是文档摆设。

---

## 改造点 3：增强 SearchRouter 的偏好/任务召回信号

现在 router 的分类词比较死，够用但不聪明。

建议：
- preference route 增加“说话方式 / 口吻 / 风格 / 回答习惯 / 输出偏好 / 不要怎样”类 token
- task route 增加“继续 / 接着 / 做到哪 / 还差什么 / 卡在哪 / 后续计划”类 token
- fact route 对 key/path/time/config 保持高精度
- history route 继续兜底 episodes + vector

另外：
- preference/task/fact 的查询结果里，可以把 graph 关联边更积极拉出来
- 提高 aliases/tags 对召回的权重

---

## 改造点 4：给 preferences/tasks/episodes 补推荐 schema 约束

当前 stores 已经能存，但字段太松，容易沦为“另一个 JSON 垃圾堆”。

建议至少在文档和 helper 层统一模板。

### preference 推荐模板
```json
{
  "key": "user.communication_style",
  "summary": "用户偏好直接、高效、少废话的沟通方式",
  "scope": "global",
  "importance": "high",
  "status": "active",
  "aliases": ["直接一点", "少废话", "高效沟通"],
  "tags": ["communication", "style"],
  "evidence": "USER.md / direct user instruction",
  "last_verified": "..."
}
```

### task 推荐模板
```json
{
  "task_id": "task.claw-memory-layering",
  "title": "完善记忆分层与治理能力",
  "goal": "让结构化记忆真正承接偏好/任务/事件",
  "state": "active",
  "priority": "high",
  "next_step": "补治理报告和迁移候选流",
  "blockers": [],
  "related_entities": ["claw-memory-system", "OpenClaw"],
  "last_active_at": "..."
}
```

### episode 推荐模板
```json
{
  "episode_id": "episode.disable-autorecall-2026-03",
  "title": "关闭 autoRecall 以降低噪声",
  "episode_type": "decision",
  "summary": "因为低相关记忆反复注入系统消息，最终关闭 autoRecall",
  "decision": "暂时关闭 autoRecall",
  "impact": "改为手动 recall / cron recall",
  "related_fact_keys": ["memory.min_score"],
  "related_task_ids": ["task.claw-memory-layering"],
  "tags": ["memory", "retrieval", "noise"]
}
```

---

## 改造点 5：建立“结构化优先，文本兜底”的工作流

推荐工作顺序：

1. 当天发生的事先记到 daily memory
2. 通过候选提炼器识别高价值记录
3. 确认后写入 facts / preferences / tasks / episodes
4. 定期更新 MEMORY.md 摘要
5. 重建 graph / index

这才是稳的。

---

## 四、建议的分阶段实施计划

## Phase 1：先把规范落地
- 完成记忆写入规范文档
- 给当前工作区做主题映射
- 指出哪些内容应该迁到 preference/task/episode

## Phase 2：补治理能力
- 增加 memory governance report
- 增加 layered migration candidate 生成器
- 增加冲突检查

## Phase 3：补检索体验
- 强化 SearchRouter 分类词
- 对 aliases/tags 做更高权重
- 更主动利用 graph 扩展 preference/task/fact 命中

## Phase 4：把 repo 改动同步到 OpenClaw 实际扩展目录
- 修改 repo：`/Users/jiangjk/dev/project/github/claw-memory-system`
- 测试通过后同步到：`/Users/jiangjk/.openclaw/extensions/claw-memory-system`
- 必要时重启 gateway

---

## 五、对你当前环境最值的三个动作

### 动作 1
先把这份规范作为团队内“主规则”。

### 动作 2
把现有长期信息迁一轮：
- 从 memory tool / MEMORY.md / daily memory 中挑出 preference/task/episode 候选

### 动作 3
在 claw-memory-system 里补一个治理报告和分层候选提炼器。

这个最有产出，也最能把第一第三点串起来。

---

## 最后一句

当前方案不是没能力，而是**结构化层没真正接管记忆治理**。

把“规范 + 治理 + 提炼”三件事补上，它就会从“能存”升级成“能长期协作”。
