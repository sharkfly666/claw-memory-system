# `memos-local` 存量记忆迁移到 `memory-pro`

这份文档只解决一件事：

> 把 `~/.openclaw/memos-local/memos.db` 里的历史记忆，批量迁移到当前由 `memory-lancedb-pro` 驱动的 `memory-pro` live store。

它不是 facts 迁移，也不是 `MEMORY.md` 清洗，而是 **旧 SQLite 记忆库 -> 当前语义记忆库** 的导入流程。

---

## 先讲清楚两套存储

### `memos-local`

- 典型路径：`~/.openclaw/memos-local/memos.db`
- 存储形态：SQLite
- 这次确认过的历史大量会话记录，就在这里

### `memory-pro`

- 典型路径：`~/.openclaw/memory/lancedb-pro/`
- 存储形态：LanceDB / `memory-lancedb-pro`
- 这是 OpenClaw 当前在线使用的语义记忆库

### 结论

如果你发现：

- `memory-pro stats --json` 数量不多
- 但 `memos.db` 里有上千条历史记录

这并不矛盾，因为它们本来就不是同一个库。

---

## 当前推荐的 canonical 导入规则

默认只导入：

```text
dedup_status = active
```

原因：

- `active` 代表当前 dedup 后保留下来的 canonical 记忆
- `duplicate` 通常是重复项，不应该再次导入
- `merged` 在当前数据里通常已经被 `active` 存活项吸收，不适合作为默认导入集合

如果你没有很强的业务理由，不建议放宽这个规则。

---

## 文本映射规则

导入时采用：

- 优先使用 `summary` -> `memory-pro.text`
- 如果 `summary` 为空或只有单字符，则回退到 `content`
- 原始 `content` -> `metadata.legacy.content`

这样做的原因是：

- `summary` 更适合作为语义检索的主文本
- 某些旧记录的 `summary` 只是 `"2"`、`"3"` 这类占位字符，不能直接作为语义文本
- 原始长文本仍然保存在 metadata 里，方便追溯

---

## scope 映射规则

- `owner = public` -> `global`
- 其他 owner 值 -> 原样映射为 `memory-pro scope`

这就是为什么导入时需要按 scope 拆成多个 JSON 文件，再逐个执行 `openclaw memory-pro import --scope ...`。

---

## 第 1 步：先做备份

真实导入前，至少备份两份东西：

### 1. 导出当前 live store

```bash
cd ~/.openclaw/workspace
openclaw memory-pro export --output /tmp/memory-pro-before-memos-import.json
```

### 2. 备份当前 LanceDB 目录

```bash
mkdir -p /tmp/memory-pro-before-memos-import
rsync -a ~/.openclaw/memory/lancedb-pro/ /tmp/memory-pro-before-memos-import/lancedb-pro/
```

如果你的 `openclaw` 依赖 Node 22+，确保命令运行时使用正确的 Node 版本。

---

## 第 2 步：先做 preview / dry-run

```bash
cd /path/to/claw-memory-system
python3 scripts/run_memos_local_migration_preview.py \
  --db ~/.openclaw/memos-local/memos.db \
  --out-dir /tmp/memos-local-migration-preview \
  --workspace ~/.openclaw/workspace \
  --openclaw-bin openclaw
```

你会得到：

- 每个 scope 一个导入文件
- 一份 JSON summary
- 对每个 scope 执行一次 `openclaw memory-pro import --dry-run`

常见输出重点：

- `canonical_chunk_count`
- `payloads.<scope>.count`
- `dry_run.results.<scope>.planned`

---

## 第 3 步：执行真实导入

```bash
cd /path/to/claw-memory-system
python3 scripts/run_memos_local_import.py \
  --db ~/.openclaw/memos-local/memos.db \
  --out-dir /tmp/memos-local-migration-import \
  --workspace ~/.openclaw/workspace \
  --openclaw-bin openclaw \
  --execute
```

注意：

- 没有 `--execute` 时，脚本会直接拒绝执行
- 这是故意的安全阀，避免误写 live store

真实导入时，脚本会：

1. 读取 canonical chunks
2. 按 scope 生成 payload
3. 对每个 scope 执行一次真实 `openclaw memory-pro import`
4. 输出结构化 JSON 结果

你重点看：

- `import.results.<scope>.ok`
- `import.results.<scope>.imported`
- `import.results.<scope>.skipped`

---

## 第 4 步：导入后验证

### 看总量

```bash
cd ~/.openclaw/workspace
openclaw memory-pro stats --json
```

### 看实际条目

```bash
cd ~/.openclaw/workspace
openclaw memory-pro list --scope agent:main --limit 5 --json
```

### 做一次检索验证

```bash
cd ~/.openclaw/workspace
openclaw memory-pro search "部署管理系统查看数据" --scope agent:main --limit 3 --json
```

如果检索结果中出现：

- `id` 形如 `memos-local:chunk:...`
- 文本来自原 `summary`，或者在 `summary` 太短时回退到 `content`
- metadata 中保留了原始 `content`

说明迁移已经真正进 live store，而不是只生成了中间文件。

---

## 已知注意事项

### 1. `memory-pro migrate check` 不是 `memos.db` 迁移器

`openclaw memory-pro migrate check` 主要覆盖的是 legacy LanceDB 迁移链路。

它**不会**自动读取 `~/.openclaw/memos-local/memos.db`。

所以 `memos-local` 的导入必须走本仓库这套脚本。

### 2. 极短文本可能会被 `memory-pro` 跳过

如果某些 chunk 的 `summary/content` 太短，`memory-pro import` 可能会把它们记为 skipped。

这是导入器自身的保护逻辑，不是本仓库 payload 生成失败。

如果是这种情况，先分两类看：

- `summary` 和 `content` 都很短，比如 `"B"`、`"2"`，这类通常就是噪音，继续跳过即可
- `summary` 很短，但 `content` 实际是完整文本，这类应该用当前脚本重新导出后再做定向补录

### 3. 默认不要导入 `duplicate` / `merged`

除非你确定要保留重复历史，否则继续坚持 `active only`。

---

## 定向补录一条 skipped 记忆

如果你已经完成过一次批量导入，后续才发现：

- 某条 skipped 记录的 `summary` 很短
- 但 `content` 是完整有效记忆

可以按下面的方式只补这一条，不需要整批重导。

### 第 1 步：用当前映射逻辑导出单条 payload

```bash
cd /path/to/claw-memory-system
python3 - <<'PY'
from pathlib import Path
import json
import sqlite3
import sys

repo = Path('/path/to/claw-memory-system')
sys.path.insert(0, str(repo / 'src'))
from claw_memory_system.memos_local_migration import row_to_memory

row_id = '替换成实际 chunk id'
db = Path('~/.openclaw/memos-local/memos.db').expanduser()
out = Path('/tmp/memos-local-targeted.json')

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
try:
    row = conn.execute(
        '''
        select id, session_key, turn_id, seq, role, content, kind, summary,
               created_at, updated_at, task_id, skill_id, merge_count,
               last_hit_at, merge_history, dedup_status, dedup_target,
               dedup_reason, owner
        from chunks
        where id = ?
        ''',
        (row_id,),
    ).fetchone()
finally:
    conn.close()

memory = row_to_memory(dict(row), source_db=db)
scope = memory.pop('scope')
out.write_text(json.dumps({'memories': [memory]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str(out), 'scope': scope, 'id': memory['id']}, ensure_ascii=False))
PY
```

### 第 2 步：先 dry-run

```bash
cd ~/.openclaw/workspace
openclaw memory-pro import /tmp/memos-local-targeted.json --scope agent:main --dry-run
```

确认输出类似：

```text
Would import 1 memories
```

### 第 3 步：再做真实导入

```bash
cd ~/.openclaw/workspace
openclaw memory-pro import /tmp/memos-local-targeted.json --scope agent:main
```

### 第 4 步：导入后核验

至少做两种验证：

- `openclaw memory-pro stats --json`
- `openclaw memory-pro export --output /tmp/memory-pro-post-targeted.json`

第二种验证的价值是：

- 可以按 exact `id` 检查目标记忆是否真的进入 live store
- 可以确认 `text` 已经是回退后的完整 `content`

这种定向补录只适合极少量漏导项，不适合作为常规批量迁移方式。

---

## 推荐操作顺序

```text
备份 live store
  -> preview / dry-run
  -> 真实 import
  -> stats/list/search 验证
  -> 再跑一次 deep integration check
```

这套顺序是当前最稳的收口方式。
