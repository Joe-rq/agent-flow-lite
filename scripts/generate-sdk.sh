#!/bin/bash
# SDK 生成脚本
# 使用前确保后端运行在 localhost:8000

set -e

BACKEND_URL="http://localhost:8000"
OPENAPI_SPEC="${BACKEND_URL}/openapi.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SDKS_DIR="${PROJECT_ROOT}/sdks"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== SDK 生成脚本 ===${NC}"

# 检查后端是否运行
echo -e "\n${YELLOW}检查后端状态...${NC}"
if ! curl -s -f "${OPENAPI_SPEC}" > /dev/null 2>&1; then
    echo -e "${RED}错误: 后端未运行或 OpenAPI spec 不可用${NC}"
    echo -e "${YELLOW}请先启动后端: cd backend && uv run uvicorn main:app --reload${NC}"
    exit 1
fi
echo -e "${GREEN}后端运行正常${NC}"

# 创建 SDK 目录
mkdir -p "${SDKS_DIR}/python" "${SDKS_DIR}/typescript"

# 下载 OpenAPI spec
curl -s "${OPENAPI_SPEC}" -o "${SDKS_DIR}/openapi.json"
echo -e "${GREEN}OpenAPI spec 已下载: ${SDKS_DIR}/openapi.json${NC}"

# 生成 TypeScript 类型定义
echo -e "\n${YELLOW}生成 TypeScript 类型定义...${NC}"
if command -v npx &> /dev/null; then
    npx openapi-typescript "${SDKS_DIR}/openapi.json" -o "${SDKS_DIR}/typescript/schema.d.ts"
    echo -e "${GREEN}TypeScript 类型生成完成${NC}"
else
    echo -e "${RED}npx 不可用，跳过 TypeScript 类型生成${NC}"
fi

# Python SDK 是手写的简单客户端，无需生成
echo -e "\n${YELLOW}Python SDK 使用手写客户端 (sdks/python/client.py)${NC}"

echo -e "\n${GREEN}=== 完成 ===${NC}"
echo -e "Python SDK: ${SDKS_DIR}/python/client.py"
echo -e "TypeScript SDK: ${SDKS_DIR}/typescript/client.ts"
echo -e "TypeScript 类型: ${SDKS_DIR}/typescript/schema.d.ts"
