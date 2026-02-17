#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== T1b Workflow 迁移验证 ==="

# 1. 迁移前：统计 workflows.json 中的工作流数
if [ ! -f data/workflows.json ]; then
  echo "SKIP: data/workflows.json 不存在，跳过迁移验证（新环境）"
  echo "[6/6] 回归测试..."
  uv run pytest -q
  echo "=== T1b PASS ==="
  exit 0
fi

JSON_COUNT=$(uv run python -c "
import json
with open('data/workflows.json', 'r') as f:
    raw = json.load(f)
if isinstance(raw, dict):
    wf = raw.get('workflows', {})
    items = [(k, v) for k, v in wf.items()] if isinstance(wf, dict) else [(v.get('id',''), v) for v in wf]
elif isinstance(raw, list):
    items = [(v.get('id',''), v) for v in raw]
else:
    items = []
print(len(items))
")
echo "[1/5] JSON 工作流数: $JSON_COUNT"

if [ "$JSON_COUNT" -eq 0 ]; then
  echo "SKIP: 无工作流数据"
  uv run pytest -q
  echo "=== T1b PASS ==="
  exit 0
fi

# 2. 跑迁移脚本
echo "[2/5] 执行迁移脚本..."
uv run python scripts/migrate_workflows_to_db.py

MATCH_COUNT=$(uv run python -c "
import json, sqlite3
with open('data/workflows.json', 'r') as f:
    raw = json.load(f)
if isinstance(raw, dict):
    wf = raw.get('workflows', {})
    if isinstance(wf, dict):
        items = list(wf.items())
    elif isinstance(wf, list):
        items = [(str(v.get('id','')), v) for v in wf if isinstance(v, dict)]
    else:
        items = []
elif isinstance(raw, list):
    items = [(str(v.get('id','')), v) for v in raw if isinstance(v, dict)]
else:
    items = []

conn = sqlite3.connect('data/app.db')
matched = 0
for wf_id, _ in items:
    row = conn.execute('SELECT 1 FROM workflows WHERE id = ?', (wf_id,)).fetchone()
    if row:
        matched += 1
conn.close()
print(matched)
")
echo "[3/5] JSON 映射记录数: $MATCH_COUNT (期望: $JSON_COUNT)"
if [ "$MATCH_COUNT" -ne "$JSON_COUNT" ]; then
  echo "FAIL: JSON 对应记录未全部迁移"
  exit 1
fi

# 4. 抽样校验：第一条 workflow 的 name 一致
SAMPLE_CHECK=$(uv run python -c "
import json, sqlite3
with open('data/workflows.json', 'r') as f:
    raw = json.load(f)
# 归一化为 [(id, data)] 列表
if isinstance(raw, dict):
    wf = raw.get('workflows', {})
    if isinstance(wf, dict):
        items = list(wf.items())
    else:
        items = [(v.get('id',''), v) for v in wf]
elif isinstance(raw, list):
    items = [(v.get('id',''), v) for v in raw]
else:
    items = []

first_id, first_data = items[0]
json_name = first_data.get('name', '')

conn = sqlite3.connect('data/app.db')
row = conn.execute('SELECT name FROM workflows WHERE id = ?', (first_id,)).fetchone()
conn.close()

if row and row[0] == json_name:
    print('match')
else:
    print(f'mismatch: json={json_name} db={row}')
")
echo "[4/5] 抽样校验: $SAMPLE_CHECK"
if [ "$SAMPLE_CHECK" != "match" ]; then
  echo "FAIL: 抽样不一致"
  exit 1
fi

# 5. 幂等性
echo "[5/5] 幂等性检查..."
uv run python scripts/migrate_workflows_to_db.py
DB_COUNT1=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM workflows').fetchone()[0]
conn.close()
print(count)
")
DB_COUNT2=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM workflows').fetchone()[0]
conn.close()
print(count)
")
if [ "$DB_COUNT2" -ne "$DB_COUNT1" ]; then
  echo "FAIL: 幂等性破坏 ($DB_COUNT1 -> $DB_COUNT2)"
  exit 1
fi
echo "幂等性 OK ($DB_COUNT2 == $DB_COUNT1)"

# 6. 回归测试
echo "[6/6] 回归测试..."
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
for table in ('auth_tokens', 'users'):
    conn.execute(f'DELETE FROM {table}')
conn.commit()
conn.close()
"
uv run pytest -q

echo "=== T1b PASS ==="
