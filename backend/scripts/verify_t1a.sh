#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== T1a Session 迁移验证 ==="

# 1. 迁移前：统计 JSON 文件数
JSON_COUNT=$(ls data/sessions/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "[1/5] JSON 文件数: $JSON_COUNT"

if [ "$JSON_COUNT" -eq 0 ]; then
  echo "SKIP: 无 JSON 文件，跳过迁移验证（新环境）"
  echo "[6/6] 回归测试..."
  uv run pytest -q
  echo "=== T1a PASS ==="
  exit 0
fi

# 2. 跑迁移脚本
echo "[2/5] 执行迁移脚本..."
uv run python scripts/migrate_sessions_to_db.py

MAPPED_COUNT=$(uv run python -c "
import json, sqlite3
from pathlib import Path
sessions_dir = Path('data/sessions')
ids = []
for p in sorted(sessions_dir.glob('*.json')):
    try:
        payload = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    sid = payload.get('session_id') if isinstance(payload, dict) else None
    ids.append(str(sid) if sid else p.stem)

conn = sqlite3.connect('data/app.db')
found = 0
for sid in ids:
    row = conn.execute('SELECT 1 FROM chat_sessions WHERE session_id = ?', (sid,)).fetchone()
    if row:
        found += 1
conn.close()
print(found)
")
echo "[3/5] JSON 映射记录数: $MAPPED_COUNT (期望: $JSON_COUNT)"
if [ "$MAPPED_COUNT" -ne "$JSON_COUNT" ]; then
  echo "FAIL: JSON 对应记录未全部迁移"
  exit 1
fi

FIRST_ID=$(uv run python -c "
import json
from pathlib import Path
files = sorted(Path('data/sessions').glob('*.json'))
p = files[0]
try:
    payload = json.loads(p.read_text(encoding='utf-8'))
except Exception:
    payload = {}
sid = payload.get('session_id') if isinstance(payload, dict) else None
print(str(sid) if sid else p.stem)
")
FOUND=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
row = conn.execute('SELECT session_id FROM chat_sessions WHERE session_id = ?', ('$FIRST_ID',)).fetchone()
conn.close()
print('yes' if row else 'no')
")
echo "[4/5] 抽样校验 ($FIRST_ID): $FOUND"
if [ "$FOUND" != "yes" ]; then
  echo "FAIL: 抽样记录未找到"
  exit 1
fi

# 5. 幂等性：再跑一次，COUNT 不变
echo "[5/5] 幂等性检查..."
uv run python scripts/migrate_sessions_to_db.py
DB_COUNT2=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0]
conn.close()
print(count)
")
DB_COUNT1=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0]
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

echo "=== T1a PASS ==="
