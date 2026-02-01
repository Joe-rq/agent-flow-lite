#!/bin/bash

# Agent Flow Lite 一键启动脚本
# 同时启动后端 FastAPI 和前端 Vue

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动 Agent Flow Lite${NC}"
echo "================================"

# 检查并激活后端虚拟环境
if [ -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${YELLOW}📦 激活后端虚拟环境...${NC}"
    source "$BACKEND_DIR/.venv/bin/activate"
else
    echo -e "${RED}❌ 后端虚拟环境不存在，请先运行 ./install.sh${NC}"
    exit 1
fi

# 检查前端依赖
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}📦 安装前端依赖...${NC}"
    cd "$FRONTEND_DIR"
    npm install
fi

# 启动后端 (在后台)
echo -e "${GREEN}🔧 启动后端服务...${NC}"
cd "$BACKEND_DIR"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 2

# 启动前端 (在后台)
echo -e "${GREEN}🎨 启动前端服务...${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

echo ""
echo "================================"
echo -e "${GREEN}✅ 服务启动完成！${NC}"
echo ""
echo -e "  ${BLUE}后端:${NC} http://localhost:8000"
echo -e "  ${BLUE}前端:${NC} http://localhost:5173"
echo -e "  ${BLUE}API文档:${NC} http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 保存 PID 到文件
echo "$BACKEND_PID $FRONTEND_PID" > "$PROJECT_ROOT/.startup_pids"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f $PROJECT_ROOT/.startup_pids; exit" INT
wait
