#!/bin/bash

# 最终 CI 验证尝试
# 尝试所有可能的方法

echo "================================"
echo "最终 CI 验证尝试"
echo "================================"
echo ""

# 方法 1: 检查 GitHub CLI 登录状态
echo "方法 1: GitHub CLI"
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI 已登录"
    echo ""
    
    # 获取 CI 状态
    RUN_INFO=$(gh run list --workflow=quality-gate.yml --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId)
    STATUS=$(echo "$RUN_INFO" | jq -r '.[0].status')
    CONCLUSION=$(echo "$RUN_INFO" | jq -r '.[0].conclusion // "pending"')
    
    echo "状态: $(echo $STATUS | tr '[:lower:]' '[:upper:]')"
    echo "结论: $(echo $CONCLUSION | tr '[:lower:]' '[:upper:]')"
    echo ""
    
    if [[ "$STATUS" == "completed" ]]; then
        if [[ "$CONCLUSION" == "success" ]]; then
            echo "================================"
            echo "✅ 成功！CI 全部通过"
            echo "================================"
            echo ""
            echo "请更新计划文件："
            echo "  .sisyphus/plans/post-gate-stability-quick-pass.md"
            echo ""
            echo "将所有 \"- [ ]\" 改为 \"- [x]\""
            exit 0
        else
            echo "================================"
            echo "❌ 失败！CI 检查未全部通过"
            echo "================================"
            echo ""
            exit 1
        fi
    else
        echo "⏳ CI 执行中，请稍后重试"
        exit 1
    fi
else
    echo "❌ GitHub CLI 未登录"
fi
echo ""

# 方法 2: 检查环境变量
echo "方法 2: 环境变量"
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GITHUB_TOKEN 环境环境变量已设置"
    echo ""
    echo "可以使用 GITHUB_TOKEN 访问 GitHub API"
    echo "但需要实现 API 调用逻辑"
else
    echo "❌ GITHUB_TOKEN 环境变量未设置"
fi
echo ""

# 方法 3: 检查 git credential helper
echo "方法 3: Git Credential Helper"
CRED_HELPER=$(git config --get credential.helper 2>/dev/null || echo "none")
echo "Credential helper: $CRED_HELPER"
echo ""

# 方法 4: 提供手动指导
echo "方法 4: 手动验证指南"
echo "================================"
echo ""
echo "🔗 访问以下链接："
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
echo "================================"
echo "结论"
echo "================================"
echo ""
echo "❌ 无法程序化验证 CI 状态"
echo ""
echo "原因："
echo "  1. GitHub CLI 未登录"
echo "  2. GITHUB_TOKEN 环境变量未设置"
echo "  3. GitHub API 速率限制"
echo ""
echo "解决方案："
echo "  1. 登录 GitHub CLI: gh auth login"
echo "  2. 设置环境变量: export GITHUB_TOKEN=your_token"
echo "  3. 手动访问并验证 CI 状态"
echo ""
echo "手动完成后，请更新计划文件："
echo "  .sisyphus/plans/post-gate-stability-quick-pass.md"
echo ""
exit 1
