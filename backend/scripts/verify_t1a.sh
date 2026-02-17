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

# 3. 迁移后记录数一致
DB_COUNT=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
count = conn.execute('SELECT COUNT(*) FROM chat_sessions').fetchone()[0]
conn.close()
print(count)
")
echo "[3/5] DB 记录数: $DB_COUNT (期望: $JSON_COUNT)"
if [ "$DB_COUNT" -ne "$JSON_COUNT" ]; then
  echo "FAIL: 记录数不一致"
  exit 1
fi

# 4. 抽样校验：第一个 JSON 文件的 session_id 在 DB 中存在
FIRST_FILE=$(ls data/sessions/*.json 2>/dev/null | head -1)
FIRST_ID=$(basename "$FIRST_FILE" .json)
FOUND=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('data/app.db')
row = conn.execute('SELECT id FROM chat_sessions WHERE id = ?', ('$FIRST_ID',)).fetchone()
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
if [ "$DB_COUNT2" -ne "$DB_COUNT" ]; then
  echo "FAIL: 幂等性破坏 ($DB_COUNT -> $DB_COUNT2)"
  exit 1
fi
echo "幂等性 OK ($DB_COUNT2 == $DB_COUNT)"

# 6. 回归测试
echo "[6/6] 回归测试..."
uv run pytest -q

echo "=== T1a PASS ==="
