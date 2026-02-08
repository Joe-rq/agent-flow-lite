#!/bin/bash
# Quality Gate 本地验证脚本
# 用途：在推送前验证所有关键检查是否通过

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Quality Gate 本地验证"
echo "========================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 结果追踪
BACKEND_PASSED=0
FRONTEND_PASSED=0

# ============================================================================
# 后端关键测试
# ============================================================================
echo "📦 后端关键测试 (Backend Critical Tests)"
echo "----------------------------------------"

cd "$PROJECT_ROOT/backend"

echo "→ 安装依赖..."
if uv sync --group dev > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 依赖安装成功"
else
    echo -e "${RED}✗${NC} 依赖安装失败"
    exit 1
fi

echo "→ 运行 P0 测试..."
if uv run pytest -q \
    tests/test_auth.py \
    tests/test_chat_citation.py \
    tests/test_chat_scoped.py \
    tests/test_workflow_api.py \
    tests/test_knowledge_dimension_mismatch.py 2>&1 | tee /tmp/backend-test-output.txt; then

    # 提取测试数量
    PASSED=$(grep -oE '[0-9]+ passed' /tmp/backend-test-output.txt | grep -oE '[0-9]+' || echo "0")
    echo -e "${GREEN}✓${NC} 后端测试通过: $PASSED 个测试"
    BACKEND_PASSED=1
else
    echo -e "${RED}✗${NC} 后端测试失败"
    BACKEND_PASSED=0
fi

echo ""

# ============================================================================
# 前端关键测试
# ============================================================================
echo "🎨 前端关键测试 (Frontend Critical Tests)"
echo "----------------------------------------"

cd "$PROJECT_ROOT/frontend"

echo "→ 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "→ 安装依赖..."
    npm ci > /dev/null 2>&1
fi

echo "→ TypeScript 类型检查..."
if npm run type-check > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 类型检查通过"
else
    echo -e "${RED}✗${NC} 类型检查失败"
    exit 1
fi

echo "→ 构建检查..."
if npm run build-only > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 构建成功"
else
    echo -e "${RED}✗${NC} 构建失败"
    exit 1
fi

echo "→ 运行 P0 测试..."
if npm run test -- --run --isolate \
    src/__tests__/App.spec.ts \
    src/__tests__/views/ChatTerminal.spec.ts \
    src/__tests__/auth/login.spec.ts 2>&1 | tee /tmp/frontend-test-output.txt; then

    # 提取测试数量
    PASSED=$(grep -oE '[0-9]+ passed' /tmp/frontend-test-output.txt | grep -oE '[0-9]+' | head -1 || echo "0")
    echo -e "${GREEN}✓${NC} 前端测试通过: $PASSED 个测试"
    FRONTEND_PASSED=1
else
    echo -e "${RED}✗${NC} 前端测试失败"
    FRONTEND_PASSED=0
fi

echo ""

# ============================================================================
# 汇总结果
# ============================================================================
echo "📊 Quality Gate 汇总"
echo "===================="
echo ""

if [ $BACKEND_PASSED -eq 1 ] && [ $FRONTEND_PASSED -eq 1 ]; then
    echo -e "${GREEN}✓ PASS - 所有关键检查通过${NC}"
    echo ""
    echo "✅ 可以安全推送到远程仓库"
    echo ""
    echo "下一步："
    echo "  git push origin main"
    echo "  然后访问: https://github.com/Joe-rq/agent-flow-lite/actions"
    exit 0
else
    echo -e "${RED}✗ FAIL - 部分关键检查失败${NC}"
    echo ""
    echo "失败的检查："
    [ $BACKEND_PASSED -eq 0 ] && echo "  - 后端关键测试"
    [ $FRONTEND_PASSED -eq 0 ] && echo "  - 前端关键测试"
    echo ""
    echo "❌ 请修复失败的测试后再推送"
    exit 1
fi
