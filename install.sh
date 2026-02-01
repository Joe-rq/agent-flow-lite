#!/bin/bash

# Agent Flow Lite 安装脚本
# 安装所有依赖

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}📦 安装 Agent Flow Lite 依赖${NC}"
echo "================================"

# 安装后端依赖
echo -e "${YELLOW}🐍 安装后端依赖...${NC}"
if [ -d "$BACKEND_DIR/.venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    cd "$BACKEND_DIR"
    uv venv .venv
fi
source "$BACKEND_DIR/.venv/bin/activate"
uv pip install -e .

# 安装前端依赖
echo -e "${YELLOW}📦 安装前端依赖...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "node_modules 已存在，跳过"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo ""
echo "运行 ./start.sh 启动服务"
