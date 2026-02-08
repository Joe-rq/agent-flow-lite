#!/bin/bash
# check-ci.sh - 本地检查 GitHub CI 状态

set -e

REPO="Joe-rq/agent-flow-lite"
BRANCH=$(git branch --show-current)

echo "🔍 检查分支: $BRANCH 的 CI 状态..."

# 获取最新 run 状态
LATEST_RUN=$(gh run list --branch "$BRANCH" --limit 1 --json status,conclusion,workflowName,url -q '.[0]')

if [ -z "$LATEST_RUN" ]; then
    echo "❌ 未找到该分支的 CI 运行记录"
    exit 1
fi

STATUS=$(echo $LATEST_RUN | jq -r '.status')
CONCLUSION=$(echo $LATEST_RUN | jq -r '.conclusion')
WORKFLOW=$(echo $LATEST_RUN | jq -r '.workflowName')
URL=$(echo $LATEST_RUN | jq -r '.url')

echo "📋 Workflow: $WORKFLOW"
echo "🔄 状态: $STATUS"
echo "✅ 结论: $CONCLUSION"
echo "🔗 链接: $URL"

if [ "$CONCLUSION" == "failure" ]; then
    echo ""
    echo "❌ CI 失败，正在获取日志..."
    gh run view --failed --exit-status || true
    exit 1
elif [ "$CONCLUSION" == "success" ]; then
    echo "✅ CI 通过！"
    exit 0
else
    echo "⏳ CI 仍在运行中..."
    gh run watch
fi
