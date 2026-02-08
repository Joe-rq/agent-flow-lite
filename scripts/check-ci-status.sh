#!/bin/bash

# CI 状态检查脚本
# 需要 GitHub CLI 登录

echo "================================"
echo "CI 状态检查"
echo "================================"
echo ""

# 检查 GitHub CLI 登录状态
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI 未登录"
    echo ""
    echo "请运行以下命令登录："
    echo "  gh auth login"
    echo ""
    echo "登录后重新运行此脚本："
    echo "  bash scripts/check-ci-status.sh"
    echo ""
    exit 1
fi

echo "✅ GitHub CLI 已登录"
echo ""

# 获取最新的工作流运行
echo "📋 获取最新的工作流运行..."
RUN_INFO=$(gh run list --workflow=quality-gate.yml --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId)

echo "$RUN_INFO" | jq -r '
  "Workflow: " + .[0].displayTitle,
  "Status: " + (.[0].status | ascii_upcase),
  "Conclusion: " + (.[0].conclusion // "pending"),
  "Created: " + .[0].createdAt,
  "Run ID: " + (.[0].databaseId | tostring)
'

echo ""
echo "================================"
echo "Job 状态"
echo "================================"
echo ""

# 获取最新运行的 job 状态
RUN_ID=$(echo "$RUN_INFO" | jq -r '.[0].databaseId')
gh run view "$RUN_ID" 2>/dev/null || echo "无法获取 job 详细信息"

echo ""
echo "================================"
echo "详细信息"
echo "================================"
echo ""

echo "🔗 查看详情："
echo "  https://github.com/Joe-rq/agent-flow-lite/actions/runs/$RUN_ID"
echo ""

