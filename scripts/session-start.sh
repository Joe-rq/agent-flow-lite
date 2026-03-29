#!/bin/bash
# Harness Lab 会话启动脚本
# 在每次会话开始时输出当前状态

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT_DIR" ]; then
  echo "⚠️ 无法确定仓库根目录"
  exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔄 Harness Lab 会话启动"
echo "════════════════════════════════════════════════════════════"

# 读取 progress.txt
PROGRESS_FILE="$ROOT_DIR/.claude/progress.txt"
if [ -f "$PROGRESS_FILE" ]; then
  echo ""
  echo "📋 当前进度："
  # 提取关键信息
  grep -E "^(Current|Last|Next|Recently)" "$PROGRESS_FILE" | head -10
else
  echo "⚠️ 进度文件不存在: $PROGRESS_FILE"
fi

# 读取 INDEX.md 中的活跃 REQ
INDEX_FILE="$ROOT_DIR/requirements/INDEX.md"
if [ -f "$INDEX_FILE" ]; then
  echo ""
  echo "📌 需求索引："
  # 提取当前活跃 REQ
  sed -n '/## 当前活跃 REQ/,/^## /p' "$INDEX_FILE" | head -10
else
  echo "⚠️ 需求索引不存在: $INDEX_FILE"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ 请根据上述状态继续工作，或询问用户需要做什么"
echo "════════════════════════════════════════════════════════════"
echo ""
