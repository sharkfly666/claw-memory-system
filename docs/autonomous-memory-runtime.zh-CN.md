# Autonomous Memory Runtime（自动记忆运行时）

这份文档描述 claw-memory-system 在 OpenClaw 中的自动运行机制，目标是：

- 标准
- 可移植
- 默认安全
- 尽量少人工干预

## 一、默认运行回路

### 1. turn capture（逐轮捕获）
输入：user / assistant / tool 摘要
输出：pending turn candidates

- 由 `claw_memory_classify_turn` 做轻量分类
- 由 `claw_memory_queue_turn_candidates` 写入 `turn_candidates.json`
- 默认只入队，不直接写正式结构化层

### 2. batch governance（定时治理）
- 读取 governance drafts
- 读取 pending turn candidates
- 统一 preview / merge / apply / noop / supersede
- refresh graph
- 写 governance / batch report

### 3. compact（后续建议）
- task archive / supersede
- daily memory 提炼
- MEMORY.md 摘要更新

## 二、运行时 stores

位于：`memory-system/stores/v2/`

- `preferences.json`
- `tasks.json`
- `episodes.json`
- `skills.json`
- `session.json`
- `graph.json`
- `models.json`
- `migration_candidates.json`
- `skill_proposals.json`
- `turn_candidates.json`

### turn_candidates.json
用途：
- 存放 post-turn classifier 输出的待治理候选
- 作为结构化层前的缓冲区

建议 schema：
```json
{
  "schema_version": "turn-candidates.v1",
  "updated_at": "...",
  "candidates": [
    {
      "target_layer": "preferences",
      "summary": "以后涉及 GitHub 下载优先用 gh，不要 git clone",
      "confidence": 0.9,
      "reason": "contains stable preference markers",
      "source": "post-turn-classifier",
      "status": "pending",
      "user_text": "...",
      "assistant_text": "...",
      "tool_summary": "...",
      "suggested_id": "pref.github-download",
      "dedupe_key": "sha1...",
      "created_at": "..."
    }
  ]
}
```

状态建议：
- `pending`
- `consumed`
- `ignored`
- `superseded`

## 三、默认安全策略

### 1. 直接写结构化层的条件
默认仅在这些情况下可考虑直接写：
- 高置信度长期偏好
- 高置信度明确配置事实
- 高置信度持续任务

否则先进 `turn_candidates.json`。

### 2. batch governance 默认策略
- auto apply safe drafts: 开
- merge existing: 开
- supersede conflicts: 关（默认保守）
- equivalence noop: 开
- graph refresh: 开

### 3. 为什么保守
因为自动记忆最怕：
- 写错
- 写重复
- 把临时聊天误当长期事实

所以默认策略应当是：

> 先入队，再治理，再吸收。

## 四、OpenClaw 可用入口

### bridge tools
- `claw_memory_batch_governance`
- `claw_memory_classify_turn`
- `claw_memory_queue_turn_candidates`

### HTTP API
- `/api/governance-report`
- `/api/memory-bootstrap`
- `/api/candidate-drafts`
- `/api/candidate-draft/preview`
- `/api/candidate-draft/apply`
- `/api/supersede`
- `/api/batch-governance`

## 五、推荐默认调度

### 每 6 小时
跑 `claw_memory_batch_governance`

目标：
- 自动吸收 safe drafts
- 消费 pending turn candidates
- refresh graph
- 写 batch report

### 每天夜间（后续建议）
- compact
- archive/supersede 老 task
- MEMORY.md 摘要候选生成

## 六、可移植性原则

1. 不依赖特定用户路径或私有服务名
2. 不把个人业务语义写死进核心判断逻辑
3. 所有自动缓冲层使用版本化 JSON schema
4. 所有自动治理动作可审计、可复跑、可 noop
5. 任何高风险自动写入都应默认关闭或保守

## 七、发布前检查清单

- [ ] bootstrap 能创建所有 stores
- [ ] bridge tools 可调用
- [ ] batch governance 可在全新工作区运行
- [ ] turn candidate queue 可在全新工作区工作
- [ ] noop / dedupe / merge 全部通过测试
- [ ] docs 说明默认安全策略

## 八、当前状态
已实现：
- turn classifier
- turn candidate queue
- candidate conversion
- batch governance 吸收 queue
- dedupe
- noop equivalence skip
- cron 化 batch governance

待实现：
- 真正接入 OpenClaw turn lifecycle
- compact pipeline
- MEMORY.md 自动摘要
