#!/bin/bash

# CI 验证脚本
# 用于验证 GitHub Actions CI 执行结果

set -e

echo "================================"
echo "CI 验证助手"
echo "================================"
echo ""

echo "📋 提交信息："
git log -1 --format="%h | %s | %ad" --date=iso
echo ""

echo "🔗 GitHub Actions 链接："
echo "https://github.com/Joe-rq/agent-flow-lite/actions/workflows/quality-gate.yml"
echo ""

echo "================================"
echo "验证清单"
echo "================================"
echo ""

echo "✅ Critical Layer（必须通过）"
echo "  [ ] frontend-type-check = Success"
echo "  [ ] frontend-build = Success"
echo "  [ ] frontend-critical-tests = Success"
echo "  [ ] backend-critical-tests = Success"
echo ""

echo "✅ Frontend Full Tests（本次修复目标）"
echo "  [ ] frontend-full-tests = Success (164/164)"
echo ""

echo "✅ E2E Tests（本次修复目标）"
echo "  [ ] e2e-tests = Success (2 tests)"
echo ""

echo "================================"
echo "详细信息"
echo "================================"
echo ""

echo "📄 参考文档："
echo "  - 验证指南: .sisyphus/evidence/ci-verification-guide.md"
echo "  - 执行报告: .sisyphus/evidence/execution-complete-summary.md"
echo ""

echo "================================"
echo "使用说明"
echo "================================"
echo ""
echo "1. 访问上述 GitHub Actions 链接"
echo "2. 找到最新的工作流运行（提交 27bfb20）"
echo "3. 检查所有 job 状态"
echo "4. 根据验证清单逐项确认"
echo ""
echo "如果所有检查通过，请更新计划文件："
echo "  - .sisyphus/plans/post-gate-stability-quick-pass.md"
echo ""
echo "如果有失败，请记录到："
echo "  - .sisyphus/notepads/post-gate-stability-quick-pass/issues.md"
echo ""

