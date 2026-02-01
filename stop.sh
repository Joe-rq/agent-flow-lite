#!/bin/bash

# Agent Flow Lite 停止脚本
# 停止所有启动的服务

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$PROJECT_ROOT/.startup_pids"

if [ -f "$PID_FILE" ]; then
    PIDS=$(cat "$PID_FILE")
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo "已停止进程: $PID"
        fi
    done
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
else
    echo -e "${YELLOW}未找到运行中的服务${NC}"
fi
