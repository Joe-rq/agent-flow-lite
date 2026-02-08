#!/bin/bash

# CI 完成验证脚本
# 尝试多种方法验证 CI 状态

echo "================================"
echo "CI 完成验证"
echo "================================"
echo ""

# 方法 1: 尝试 GitHub CLI
echo "方法 1: 检查 GitHub CLI 登录状态"
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI 已登录"
    echo ""
    
    RUN_INFO=$(gh run list --workflow=quality-gate.yml --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId)
    
    echo "最新工作流信息："
    echo "$RUN_INFO" | jq -r '
      "Workflow: " + .[0].displayTitle,
      "Status: " + (.[0].status | ascii_upcase),
      "Conclusion: " + (.[0].conclusion // "pending"),
      "Created: " + .[0].createdAt,
      "Run ID: " + (.[0].databaseId | tostring)
    '
    echo ""
    
    STATUS=$(echo "$RUN_INFO" | jq -r '.[0].status')
    if [[ "$STATUS" == "completed" ]]; then
        echo "✅ CI 执行完成"
        exit 0
    else
        echo "⏳ CI 执行中或未开始"
        exit 1
    fi
else
    echo "❌ GitHub CLI 未登录"
fi
echo ""

# 方法 2: 尝试 GitHub API（使用 curl）
echo "方法 2: 尝试 GitHub API"
API_URL="https://api.github.com/repos/Joe-rq/agent-flow-lite/actions/runs?per_page=1"
RESPONSE=$(curl -s "$API_URL" 2>/dev/null)

if [[ $? -eq 0 ]]; then
    echo "✅ API 请求成功"
    echo ""
    
    # 检查是否有错误
    if echo "$RESPONSE" | jq -e '.message' >/dev/null 2>&1; then
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.message')
        echo "❌ API 错误: $ERROR_MSG"
        exit 1
    fi
    
    echo "最新工作流信息："
    echo "$RESPONSE" | jq -r '.workflow_runs[0] | 
      "Name: " + .name,
      "Status: " + (.[0].status | ascii_upcase),
      "Conclusion: " + (.[0].conclusion // "pending"),
      "Created: " + .created_at
    '
    echo ""
    
    STATUS=$(echo "$RESPONSE" | jq -r '.workflow_runs[0].status')
    if [[ "$STATUS" == "completed" ]]; then
        echo "✅ CI 执行完成"
        exit 0
    else
        echo "⏳ CI 执行中或未开始"
        exit 1
    fi
else
    echo "❌ API 请求失败"
fi
echo ""

# 方法 3: 引导手动验证
echo "方法 3: 手动验证"
echo "================================"
echo ""
echo "🔗 访问以下链接手动验证："
echo "  https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml"
echo ""
echo "📋 验证清单："
echo "  [ ] frontend-type-check = Success"
echo "  [ ] frontend-build = Success"
echo "  [ ] frontend-critical-tests = Success"
echo "  [ ] backend-critical-tests = Success"
echo "  [ ] frontend-full-tests = Success (164/164)"
echo "  [ ] e2e-tests = Success (2 tests)"
echo ""
echo "如果所有检查通过，请更新计划文件："
echo "  .sisyphus/plans/post-gate-stability-quick-pass.md"
echo ""
exit 1
