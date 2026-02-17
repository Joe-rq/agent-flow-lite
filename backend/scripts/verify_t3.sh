#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== T3 Alembic 收尾验证 ==="

EXPECTED_TABLES="users auth_tokens chat_sessions workflows"

# 1. 备份现有 DB
if [ -f data/app.db ]; then
  cp data/app.db data/app.db.bak
  echo "[1/4] 已备份 data/app.db -> data/app.db.bak"
else
  echo "[1/4] 无现有 DB，跳过备份"
fi

# 2. 空库测试
rm -f data/app.db
echo "[2/4] 已删除 DB，执行 alembic upgrade head..."
uv run alembic upgrade head

# 3. 验证所有期望的表都存在
echo "[3/4] 验证表结构..."
RESULT=$(uv run python -c "
import sqlite3, sys
conn = sqlite3.connect('data/app.db')
tables = {r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()}
conn.close()
expected = set('$EXPECTED_TABLES'.split())
missing = expected - tables
if missing:
    print(f'FAIL: missing tables: {missing}')
    sys.exit(1)
print(f'OK: {len(tables)} tables, all expected tables present')
")
echo "$RESULT"

# 4. 回归测试
echo "[4/4] 回归测试..."
uv run pytest -q

# 恢复备份
if [ -f data/app.db.bak ]; then
  mv data/app.db.bak data/app.db
  echo "已恢复备份"
fi

echo "=== T3 PASS ==="
