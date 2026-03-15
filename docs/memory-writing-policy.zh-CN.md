# Claw Memory System 记忆写入规范（实用版）

这份规范不讨论“理想中的 AGI 记忆”，只解决一个现实问题：

**什么信息该写到哪一层，才能在 OpenClaw 里长期稳定、可更新、可召回、可维护。**

结论先说：

- **事实（facts）**：写“当前真相”
- **偏好（preferences）**：写“稳定偏好/协作方式”
- **任务（tasks）**：写“当前进行中的事”
- **事件（episodes）**：写“发生过什么、为什么这样做”
- **文件记忆（MEMORY.md / memory/YYYY-MM-DD.md）**：写“人类可读上下文和叙事”
- **向量语义记忆**：只做补充召回，不当主账本

---

## 一、核心原则

### 1. 当前真相只能有一个主落点
会变化的配置、规则、路径、服务状态，不要在多个地方都当“主记录”。

错误做法：
- facts 里一条
- preference 里一条
- MEMORY.md 再写一条
- 语义记忆再存一条

这样迟早打架。

正确做法：
- 为每类信息指定一个**主层**
- 其他层只放摘要、引用、背景，不重复维护同一份真相

### 2. 能 update 就不要 store 新副本
对于会变化的信息：
- 镜像优先级
- 早报时间
- 工作目录
- 当前默认模型

优先 **update 原记录**，不要不停新增“新版同义记忆”。

### 3. 记忆分层，不求一层包打天下
当前系统不适合把所有记忆都塞给向量召回。最稳的方式是：

- **结构化层** 负责“准”
- **文件层** 负责“全”
- **语义层** 负责“找得到相关东西”

### 4. 把“偏好”和“任务状态”分开
很多系统失败就失败在把“用户喜欢什么”和“当前正在做什么”混在一起。

- “老大喜欢直接高效” → preference
- “今天在修 daily-briefing 超时” → task / episode

不要混。

---

## 二、分层写入规则

## 1) Facts：稳定事实 / 当前配置真相

适合写入：
- 固定路径
- 服务地址
- 工具入口
- 调度时间
- 当前生效的配置值
- 明确 ID / key / token 文件位置
- 已确认的长期事实

例子：
- `daily_briefing.schedule = 每天 8:00`
- `pansou.token_file = /Users/jiangjk/.openclaw/workspace/memory/pansou-token.json`
- `workspace.root = /Users/jiangjk/.openclaw/workspace`
- `pansou.mirror_priority = [daiyazhi, panhunt, ps.252035.xyz, 38.55.131.86:82]`

不适合写入：
- “老大喜欢直接一点”
- “今天我们讨论了逐玉更新”
- “这周可能想优化早报”

### Facts 写入标准
必须满足至少两条：
1. 可以被当成“当前真相”引用
2. 将来大概率还会再次被问到
3. 需要支持精确更新
4. 更像配置/事实，不像观点/过程

### Facts 维护规则
- 同 key 只保留一个 active 主记录
- 旧值进入 history 或标记 superseded
- 尽量使用稳定 key 命名，不要用自然语言整句做 key

推荐 key 风格：
- `pansou.mirror_priority`
- `daily_briefing.schedule`
- `openclaw.workspace_root`
- `agent.primary_model`

---

## 2) Preferences：稳定偏好 / 协作偏好 / 风格规则

适合写入：
- 用户沟通风格偏好
- 工具选择偏好
- 输出格式偏好
- 长期协作原则
- 明确说过“以后都这样”的规则

例子：
- 涉及 GitHub 下载优先 `gh` 而不是 `git clone`
- 不要再尝试访问 QClaw 本地路径
- 文件按长/中/短/临时周期分桶保存
- 回答风格偏直接高效，少废话

不适合写入：
- 某个任务临时 workaround
- 某天一次性要求
- 具体资源链接
- 正在进行中的修复状态

### Preferences 写入标准
必须满足至少两条：
1. 是“以后也适用”的规则
2. 明显影响后续协作方式
3. 属于偏好/约束，不是客观事实本身
4. 用户如果下次不重复说，系统也应该记得

### Preferences 字段建议
每条 preference 至少应有：
- `summary`：一句话摘要
- `scope`：global / user / agent
- `importance`：high / medium / low
- `status`：active / superseded / archived
- `aliases`：常见改写问法
- `tags`：如 `communication`, `tooling`, `storage`, `safety`
- `evidence`：来源句子或来源文件
- `last_verified`

推荐 key 风格：
- `user.communication_style`
- `user.github_download_preference`
- `user.storage_lifecycle_preference`
- `agent.forbidden_qclaw_paths`

---

## 3) Tasks：当前任务状态 / 持续协作对象

适合写入：
- 当前正在推进的任务
- 一个任务的目标、状态、阻塞、下一步
- 多轮对话还会持续引用的工作流
- 需要“从上次做到哪继续”的内容

例子：
- `daily-briefing` 正在优化超时和 Feishu 投递
- `claw-memory-system` 正在补记忆分层和评估报告能力
- `PanSou 自动追更逐玉` 是一个待观察自动化任务

不适合写入：
- 单纯历史事实
- 永久偏好
- 完全结束且不会再续写的碎片聊天

### Tasks 写入标准
满足任一强条件即可：
1. 明确“还没做完”
2. 后续一定要继续接着做
3. 需要记录 state / blockers / next_step
4. 与具体 session 无关，但跨多轮持续存在

### Tasks 最少应包含
- `title`
- `goal`
- `state`：active / blocked / done / archived
- `next_step`
- `blockers`
- `related_entities`
- `last_active_at`
- `owner_scope`

推荐 task id：
- `task.daily-briefing-stability`
- `task.claw-memory-layering`
- `task.pansou-auto-update-zhuyu`

---

## 4) Episodes：事件、决策过程、关键转折

适合写入：
- 一次重要排障过程
- 为什么从 A 改到 B
- 某次失败、修复、验证结果
- 某个任务中的关键转折点

例子：
- autoRecall 噪声过大，minScore 提到 0.6 后仍不稳，因此关闭 autoRecall
- PanSou 从 wenyuanw 切到 daiyazhi，并新增第 4 镜像
- daily-briefing 因 Feishu 审核和 timeout 做过一次收敛修复

### Episodes 的价值
它不是“当前真相”，而是回答：
- 为什么现在是这样
- 之前踩过什么坑
- 某个决策是怎么来的

### 不要把 episode 当 facts
例如：
- “曾经 minScore=0.42” 是 episode
- “当前 minScore=0.6” 才应该是 fact

---

## 5) MEMORY.md：人工可读的长期记忆摘要

适合写入：
- 少量高价值长期信息
- 人能快速扫懂的长期背景
- 比结构化字段更适合自然语言表达的长期上下文

它适合当：
- **人工审阅入口**
- **长期合作摘要**
- **结构化层的补充说明**

不适合当：
- 频繁变化配置主账本
- 任务状态机
- 大量流水日志

### MEMORY.md 最佳用途
只保留：
- 稳定服务配置摘要
- 长期协作约定
- 明显重要的结论和提醒

不要越写越像 dump。

---

## 6) memory/YYYY-MM-DD.md：日记账 / 流水层

适合写入：
- 当天发生了什么
- 做了哪些尝试
- 临时观察
- 原始上下文
- 待后续提炼的素材

这是“原料层”，不是最终层。

规则：
- 允许粗糙
- 允许冗余
- 允许叙事
- 但要定期提炼到 facts / preferences / tasks / episodes / MEMORY.md

---

## 三、落地决策树

当你准备存一条记忆时，按这个顺序问：

### Q1. 这是当前真相吗？
- 是 → facts
- 否 → 继续

### Q2. 这是长期偏好或协作规则吗？
- 是 → preferences
- 否 → 继续

### Q3. 这是正在进行、后续要接着做的事吗？
- 是 → tasks
- 否 → 继续

### Q4. 这是一次重要事件/决策过程/经验吗？
- 是 → episodes
- 否 → 继续

### Q5. 这是只是当天上下文或原始记录吗？
- 是 → `memory/YYYY-MM-DD.md`

### Q6. 这是长期摘要但不适合结构化吗？
- 是 → `MEMORY.md`

---

## 四、常见错误

### 错误 1：把偏好写成事实
例如：
- `user.prefers_direct_style = true`

这不是不能写，但语义上更应该进 preferences，不要把 facts 搞成杂货铺。

### 错误 2：把历史过程写成当前真相
例如：
- “曾经 early config 有 bug” 被当成当前配置

历史属于 episode，不是 fact。

### 错误 3：同一信息多头维护
例如 PanSou 镜像优先级：
- memory tool 一条
- MEMORY.md 一条
- skill 里一条
- task 里一条

最后根本不知道谁说了算。

### 错误 4：task 不收尾
任务结束后如果一直 active，会污染后续召回。

结束规则：
- done：完成
- archived：短期内不再管
- superseded：被新任务替代

### 错误 5：把所有东西都希望靠语义召回找回来
这就是典型自欺欺人。关键词一变就掉。

稳定配置、偏好、状态，必须有结构化落点。

---

## 五、针对当前 OpenClaw 工作区的建议映射

### 应放 facts
- 早报发送时间
- PanSou token 文件位置
- 工作区路径
- 当前 PanSou 镜像优先级
- 当前默认模型 / fallback 模型

### 应放 preferences
- 老大沟通偏好：直接、高效、少废话
- GitHub 下载优先 gh
- 不再访问 QClaw 路径
- 生成文件分桶保存策略
- PanSou 搜索优先 Quark、优先最新、先验链接有效性

### 应放 tasks
- daily-briefing 稳定性优化
- claw-memory-system 记忆分层/评估/迁移能力建设
- 某个持续数天的自动化或修复任务

### 应放 episodes
- autoRecall 调整与关闭的来龙去脉
- PanSou 镜像切换原因
- 某次 Feishu 审核/超时修复经过
- 某次模型切换、网关重启、配置修补决策

### 应留在 MEMORY.md
- 长期服务配置总览
- 重要提醒
- 已知问题摘要
- 少量高价值长期结论

### 应留在 daily memory
- 今天做了哪些排查
- 临时试验结果
- 没确认的猜测
- 聊天中冒出来但尚未提炼的信息

---

## 六、一个最实用的执行规则

如果拿不准，就用这条：

- **会变且要精确引用** → facts / tasks / preferences
- **解释为什么会这样** → episodes
- **给人看、帮人理解** → MEMORY.md
- **只是先记下来别丢** → daily memory

---

## 七、建议的后续工程动作

1. 给 preferences / tasks / episodes 增加更明确的推荐字段模板
2. 做一个“记忆分类助手”或 migration candidate 生成器
3. 对 facts / preferences 做冲突检测（同主题多条 active 提醒）
4. 增加一份 workspace 级 `memory-governance-report.json`
5. 支持把 daily memory 提炼成结构化记录的半自动流程

---

## 最后一句

**记忆系统最怕的不是记不住，而是“记了一堆，但不知道该信哪条”。**

所以优先级永远是：

**可更新 > 可检索 > 可解释 > 数量多。**
