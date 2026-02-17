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

# 3. 迁移后记录数一致
DB_COUNT=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM workflows').fetchone()[0]
conn.close()
print(count)
")
echo "[3/5] DB 记录数: $DB_COUNT (期望: $JSON_COUNT)"
if [ "$DB_COUNT" -ne "$JSON_COUNT" ]; then
  echo "FAIL: 记录数不一致"
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
DB_COUNT2=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM workflows').fetchone()[0]
conn.close()
print(count)
")
if [ "$DB_COUNT2" -ne "$DB_COUNT" ]; then
  echo "FAIL: 幂等性破坏 ($DB_COUNT -> $DB_COUNT2)"
  exit 1
fi
echo "幂等性 OK ($DB_COUNT2 == $DB_COUNT)"

# 6. 回归测试
echo "[6/6] 回归测试..."
uv run pytest -q

echo "=== T1b PASS ==="
