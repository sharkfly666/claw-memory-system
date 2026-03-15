# OpenClaw 记忆系统 V2 方案提案

> 目标：参考 MemOS 的“分层记忆 + 可观测 + 可评测 + 可演进”思想，在现有 `claw-memory-system` 基础上升级，而不是盲目重写。

## 一、问题定义

根据近期对 MemOS 的实测，当前单纯依赖语义检索类记忆会出现几个明显问题：

1. **能搜到片段，但记不住事情**
2. **对用户偏好、当前任务、近期结论的召回弱**
3. **对连续协作不友好，像“对话搜索”而不像“协作记忆”**
4. **结构化事实、路径、配置类信息还行，但任务级信息差**

这说明：

- 纯 vector / hybrid recall 不是完整记忆系统
- 需要把“事实”“偏好”“任务状态”“历史片段”拆层管理
- 需要显式的写入策略、时间策略、淘汰策略、评测策略

## 二、总体方向：在现有项目上升级，而不是推倒重来

当前 `claw-memory-system` 已经具备不错的骨架：

- facts 层
- exact search / page index
- markdown 人类可读层
- compatibility / migration
- 与 `memory-lancedb-pro` 的协同思路

因此更合理的路径是：

> **把现有项目升级为面向协作的多层记忆系统 V2**

而不是直接另起炉灶。

## 三、V2 核心设计原则

### 1. 分层而不是单库

将记忆拆成至少 6 层：

1. **事实层 Facts**
   - 当前真实状态
   - 路径、服务地址、账号信息、固定配置、稳定事实
   - 可覆盖更新，有版本和时间元数据

2. **偏好层 Preferences**
   - 用户的稳定表达偏好、协作方式偏好、输出风格偏好
   - 与 facts 分开，便于单独抽取、加权、确认和修正

3. **任务层 Tasks / Working Memory**
   - 正在进行的问题、最近结论、当前阻塞、下一步动作
   - 这是当前最缺的一层
   - 应有 `active / paused / done / abandoned` 等状态

4. **情节层 Episodes / Summaries**
   - 一次完整讨论、一次任务、一次排障、一次决策的摘要
   - 用于“记住事情”，而不是只记住句子

5. **技能层 Skills / Evolution**
   - OpenClaw 技能目录、技能来源、安装状态、使用反馈、演进提案
   - 用于把“任务经验”转成“技能资产”
   - 支持专用技能进化模型参与总结、提案、合并建议

6. **片段层 Raw Retrieval**
   - 原始对话、向量召回、历史片段
   - 用于保真和兜底，不直接承担“当前记忆”的主职责

### 2. 查询路由优先级要更明确

建议查询路由调整为：

- **用户偏好 / 如何回答** → preferences → facts → episodes
- **现在在做什么 / 刚才讨论到哪** → tasks → episodes → vector
- **某项配置 / 路径 / 名称 / ID** → facts → exact search → vector
- **某次历史讨论 / 模糊回忆** → episodes → vector → exact search
- **技能相关 / 我们有没有现成方法** → skills → episodes → vector
- **混合问题** → tasks / facts / preferences / skills 先聚合，再向 vector 补充

也就是说，

> **不要让 vector 检索直接承担任务记忆、偏好记忆和技能记忆的主入口。**

### 3. 写入不是“全量存档”，而是“分流沉淀”

每轮对话结束后，不应只把对话扔进向量库，而应做分类写入：

- 抽取稳定事实 → facts
- 抽取稳定偏好 → preferences
- 抽取当前任务状态 → tasks
- 生成本轮或本次议题摘要 → episodes
- 抽取技能候选、经验沉淀、改进建议 → skills
- 原始对话 → raw/vector

### 4. 时间和状态必须成为一等公民

每条高层记忆都应带：

- `created_at`
- `updated_at`
- `last_verified`
- `confidence`
- `scope`
- `status`
- `ttl_days`（可选）
- `superseded_by` / `supersedes`
- `source_ref`

特别是任务层，需要：

- `task_id`
- `state`
- `priority`
- `next_action`
- `last_active_at`
- `related_entities`

特别是技能层，需要：

- `skill_id`
- `installed`
- `source_task_ids`
- `quality_score`
- `usage_count`
- `last_used_at`
- `evolution_status`
- `proposed_by_model`

## 四、为什么现有项目适合做这个升级

当前项目已经有：

- `facts_store.py`：适合继续扩展 metadata 和新 store
- `pageindex.py`：适合做 exact search 和多源索引
- docs 中已经有 layered memory 思路
- migration plan 已经明确“不应把旧记忆全量复制成 facts”

因此 V2 可以沿着现有结构演进：

```text
claw-memory-system/
├── src/claw_memory_system/
│   ├── facts_store.py
│   ├── preferences_store.py      # 新增
│   ├── tasks_store.py            # 新增
│   ├── episodes_store.py         # 新增
│   ├── skills_store.py           # 新增
│   ├── extract_preference_candidates.py
│   ├── extract_task_state.py
│   ├── extract_episode_summary.py
│   ├── extract_skill_candidates.py      # 新增
│   ├── search_router.py          # 新增：统一查询路由
│   ├── evaluate_memory.py        # 新增：评测框架
│   ├── admin_api.py              # 新增：管理系统 API
│   └── ...
├── schemas/
│   ├── facts.v1.schema.json
│   ├── preferences.v1.schema.json
│   ├── tasks.v1.schema.json
│   ├── episodes.v1.schema.json
│   ├── skills.v1.schema.json     # 新增
│   └── models.v1.schema.json     # 新增：嵌入模型/摘要模型/技能进化模型配置
├── webapp/                       # 新增：管理系统前端
└── docs/
```

## 五、管理系统（类似 MemOS 的管理后台）

你提出的要求非常合理：

> V2 应提供类似 MemOS 的管理系统，便于直观查看记忆数据、手动迁移记忆，并统一管理模型配置与技能。

我建议把这块设计成 **OpenClaw Memory Console**。

### 管理系统的核心模块

#### 1. Memory Explorer
- 按层浏览：facts / preferences / tasks / episodes / skills / raw
- 支持筛选：状态、时间、来源、标签、置信度、是否过期
- 支持查看来源证据和 supersede 关系

#### 2. Migration Studio
- 从旧 memory / markdown / 向量记录中抽取候选
- 手动确认迁移到 facts / preferences / tasks / episodes / skills
- 支持批量迁移、冲突提示、预览 diff

#### 3. Retrieval Inspector
- 输入一个 query，查看路由决策
- 显示各层命中结果、得分、最终聚合结果
- 用于排查“为什么这条记忆没召回”

#### 4. Model Config Center
- 嵌入模型配置
- 摘要模型配置
- 技能进化模型配置
- 支持按用途配置不同模型与参数

#### 5. Skill Console
- 查看 OpenClaw 当前技能
- 查看技能来源（任务/经验/手工安装）
- 查看技能使用频率、效果反馈、最近调用
- 发起技能进化提案 / 审核 / 发布

#### 6. Evaluation Dashboard
- 跑标准评测集
- 对比不同版本记忆系统结果
- 查看命中率、完整性、协作可用性、偏好记忆得分等

## 六、模型配置中心（借鉴 MemOS 的优点）

你提到 MemOS 的两个增强项很好：

1. **嵌入模型配置**
2. **摘要模型配置**

我同意，而且建议 V2 再多加一个：

3. **技能进化模型配置**

### A. 嵌入模型配置（Embedding Model Profile）

用于：
- raw/vector 召回
- episode 语义检索
- 技能语义召回

建议支持：
- provider
- model name
- base URL
- API key reference
- dimensions
- batch size
- task-specific profile（query/doc 分开）
- reindex policy

### B. 摘要模型配置（Summarization Model Profile）

用于：
- episode summary 生成
- task state 压缩
- preference candidate 抽取
- migration candidate 摘要

建议支持：
- 用于短摘要 / 长摘要 / 结构化摘要的不同 profile
- 温度、最大 token、system prompt 模板
- “是否允许更新现有摘要”策略

### C. 技能进化模型配置（Skill Evolution Model Profile）

这是 V2 的特色增强。

用于：
- 从任务总结中提取技能候选
- 基于已有技能和新经验生成改进提案
- 自动对技能做重组、去重、质量评分建议

建议支持：
- 专用模型 profile
- 仅用于离线/后台，不直接参与日常对话
- 产出为“提案”，需要人工审核或半自动审核

## 七、技能管理与自动进化

你提出希望在管理系统中直接管理 OpenClaw 技能，并依托“技能进化专用模型”让技能自动进化，这个方向非常好。

### 技能层在 V2 的定位

不是简单罗列 skills，而是把它当成：

> **任务执行经验 -> 可复用技能资产**

### 建议的技能演进闭环

1. 日常任务执行产生：
   - task
   - episode summary
   - outcome
   - reusable steps

2. Skill extractor 从任务和 episode 中抽取：
   - skill candidate
   - improvement candidate
   - overlap candidate

3. Skill evolution model 生成：
   - 新技能提案
   - 现有技能修订提案
   - 合并/拆分建议

4. 管理系统中人工审核：
   - 接受
   - 修改后接受
   - 驳回

5. 发布到 skill store，并可选择：
   - 本地启用
   - 公共发布
   - 私有保存

### 管理系统中技能页应该展示

- skill_id / title / description
- source task ids
- 最近使用时间
- 使用成功率 / 人工反馈
- 当前版本
- 进化建议列表
- 是否已发布 / 是否安装

## 八、V2 的关键能力设计

### A. 偏好层（Preferences）

当前实测说明偏好记忆最弱，因此优先补这一层。

建议 schema：

```json
{
  "key": "user.communication_style.direct",
  "value": true,
  "value_type": "boolean",
  "strength": 0.9,
  "evidence": ["msg:xxx", "msg:yyy"],
  "notes": "用户偏好直接高效，不喜欢空话",
  "status": "active",
  "created_at": "...",
  "updated_at": "...",
  "last_verified": "..."
}
```

### B. 任务层（Tasks / Working Memory）

这是提升“连续协作感”的核心。

示例：

```json
{
  "task_id": "mem-eval-20260313",
  "title": "评估新 memos 记忆系统效果",
  "state": "active",
  "summary": "用户认为新 memos 不如旧方案，怀疑记忆丢失严重，已要求做 15 条实测报告。",
  "next_action": "输出问题拆解与优化建议，决定是否升级现有 claw-memory-system。",
  "related_entities": ["memos", "MemOS", "memory minScore"],
  "source_refs": ["msg:..."],
  "updated_at": "..."
}
```

### C. 情节层（Episodes）

例如：
- “Qwik 文章分析与技术选型讨论”
- “MemOS 与旧记忆方案对比评测”
- “memory minScore 调参与 Gateway 重启”

它的作用不是取代 raw memory，而是：

> 让系统在回忆时先拿到“事情”，再补原文片段。

### D. 技能层（Skills）

建议 schema 具备：

```json
{
  "skill_id": "skill-memory-eval-v1",
  "title": "评测记忆系统连续协作能力",
  "summary": "使用 15~20 条样例从偏好、任务、事实、决策四个维度评估记忆系统。",
  "installed": true,
  "source_task_ids": ["task-001"],
  "quality_score": 0.82,
  "usage_count": 5,
  "evolution_status": "active",
  "proposed_by_model": "skill-evolver-v1",
  "updated_at": "..."
}
```

## 九、建议的实现路线（分阶段）

### Phase 1：补三层 store + 技能层 + schema

优先新增：

- `preferences_store.py`
- `tasks_store.py`
- `episodes_store.py`
- `skills_store.py`
- 对应 schema

### Phase 2：补管理系统最小后台

新增：

- `admin_api.py`
- `webapp/` 前端
- Memory Explorer / Migration Studio / Model Config Center / Skill Console MVP

### Phase 3：补抽取器与路由器

- `extract_preference_candidates.py`
- `extract_task_state.py`
- `extract_episode_summary.py`
- `extract_skill_candidates.py`
- `search_router.py`

### Phase 4：补评测框架

- `evaluate_memory.py`
- 固定评测集
- 管理后台展示评测结果

### Phase 5：接入技能自动进化链路

- 技能进化专用模型
- 任务经验 -> 技能提案
- 审核与发布流程

## 十、建议优先级

### P0（必须先做）

1. preferences / tasks / episodes / skills store
2. model config center schema
3. query router MVP
4. evaluation harness
5. 管理后台 MVP（至少可浏览和手动迁移）

### P1（随后做）

1. 自动候选抽取
2. 置信度与去重
3. supersede / merge 机制
4. skill evolution proposal pipeline

### P2（后续）

1. sidecar sync
2. 自动写回 OpenClaw memory
3. 更强 rerank / retrieval fusion
4. 生命周期治理
5. 更完整权限控制与审计日志

## 十一、我推荐的决策

### 不建议

- 直接彻底重写一个“全新记忆系统”
- 用单一 vector recall 替代所有层
- 不做评测就上线
- 只做底层能力、不做管理系统和可视化

### 建议

> **以 `/Users/jiangjk/dev/project/github/claw-memory-system` 为基础升级为 OpenClaw Memory V2 + 管理控制台。**

原因：

- 已有 layered memory 骨架
- 已有 facts / exact search / migration 能力
- 更符合你之前方案的优势
- 能吸收 MemOS 的分层、演进、可视化、模型配置思想
- 还能进一步整合 OpenClaw skill 管理与技能进化
- 风险远低于从零重写

## 十二、建议的近期里程碑

### Milestone 1（1~2 天）
- 加 schema：preferences / tasks / episodes / skills / models
- 加 store：五类 JSON store
- 写最小 CLI

### Milestone 2（2~4 天）
- 做管理后台 MVP
- 支持浏览、筛选、手动迁移
- 支持模型配置录入

### Milestone 3（2~4 天）
- 做 rule-based 抽取器
- 做 search router MVP
- 跑现有 15~20 条评测样例

### Milestone 4（3~5 天）
- 接技能管理与技能进化提案
- 展示技能来源、安装状态、使用反馈

### Milestone 5
- 输出一版可真正用于 OpenClaw 的集成方案

## 十三、成功标准

V2 不应只看“能不能搜到”，而应看：

1. 偏好类记忆明显提升
2. 当前任务/近期议题召回明显提升
3. 决策/结论不再轻易丢失
4. 配置/路径查询保持稳定
5. 具备类似 MemOS 的管理可视化与手动迁移能力
6. 支持嵌入模型 / 摘要模型 / 技能进化模型三类配置
7. 技能可在管理系统中统一查看、管理、进化
8. 通过固定评测集对比当前 MemOS 有显著提升

---

如果继续推进，下一步最合理的不是继续讨论概念，而是：

1. 在当前 repo 里补三层 store + 技能层和 schema
2. 补一个最小 admin API 和管理后台骨架
3. 补一个 model config center
4. 补一个 evaluation harness
5. 用你现有 15~20 条样例持续回归测试
