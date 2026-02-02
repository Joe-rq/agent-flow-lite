#!/bin/bash

# 自动监控文件变动并提交
# 使用 fswatch 监听文件变化，自动 git add + git commit

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 检查 fswatch 是否安装
if ! command -v fswatch &> /dev/null; then
    echo -e "\033[0;31m❌ 需要安装 fswatch\033[0m"
    echo "brew install fswatch"
    exit 1
fi

echo -e "\033[0;34m👀 开始监控文件变动... (按 Ctrl+C 停止)\033[0m"
echo ""

# 忽略的文件和目录
EXCLUDE_PATTERN="node_modules|\.git|dist|\.venv|__pycache__|\.pyc"

# 上次提交时间（避免重复提交）
LAST_COMMIT_TIME=0

fswatch -r \
    --exclude="$EXCLUDE_PATTERN" \
    --include='\.(vue|ts|js|py|md|json|yaml|yml)$' \
    . | while read -r event; do
    # 获取触发变动的文件
    FILE="${event#$PROJECT_ROOT/}"

    # 跳过非项目根目录的变动
    if [[ ! -e "$FILE" ]]; then
        continue
    fi

    # 检查是否有改动
    if git diff --quiet 2>/dev/null; then
        continue
    fi

    # 获取变更文件列表
    CHANGED=$(git diff --name-only | head -5 | tr '\n' ' ')
    if [ ${#CHANGED} -gt 50 ]; then
        CHANGED="${CHANGED:0:50}..."
    fi

    # 自动 add
    git add -A 2>/dev/null

    # 生成中文 commit message
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    COMMIT_MSG="chore: 更新 ${CHANGED} - ${TIMESTAMP}"

    # 提交
    if git commit -m "$COMMIT_MSG" 2>/dev/null; then
        echo -e "\033[0;32m✅ 自动提交: $COMMIT_MSG\033[0m"

        # 自动推送到远程
        git push origin main 2>/dev/null && echo -e "\033[0;34m✅ 已推送到远程\033[0m" || echo -e "\033[0;31m❌ 推送失败\033[0m"
    fi
done
