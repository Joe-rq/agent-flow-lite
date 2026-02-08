#!/bin/bash

# CI 状态轮询脚本
# 自动检查 GitHub Actions CI 执行状态

set -e

# 配置
MAX_ATTEMPTS=30
SLEEP_INTERVAL=10
WORKFLOW="quality-gate.yml"
COMMIT="27bfb20"

echo "================================"
echo "CI 状态轮询器"
echo "================================"
echo ""
echo "配置："
echo "  工作流: $WORKFLOW"
echo "  提交: $COMMIT"
echo "  最大尝试次数: $MAX_ATTEMPTS"
echo "  轮询间隔: ${SLEEP_INTERVAL}秒"
echo ""

# 检查 GitHub CLI 登录状态
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI 未登录"
    echo ""
    echo "请运行以下命令登录："
    echo "  gh auth login"
    echo ""
    echo "或者设置环境变量："
    echo "  export GITHUB_TOKEN=your_token_here"
    echo ""
    exit 1
fi

echo "✅ GitHub CLI 已登录"
echo ""

# 轮询 CI 状态
echo "开始轮询 CI 状态..."
echo ""

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "----------------------------------------"
    echo "尝试 #$attempt / $MAX_ATTEMPTS"
    echo "----------------------------------------"
    echo ""

    # 获取最新的工作流运行
    RUN_INFO=$(gh run list --workflow="$WORKFLOW" --limit 1 --json status,conclusion,displayTitle,createdAt,databaseId,commit)
    
    # 解析信息
    STATUS=$(echo "$RUN_INFO" | jq -r '.[0].status')
    CONCLUSION=$(echo "$RUN_INFO" | jq -r '.[0].conclusion // "pending"')
    RUN_COMMIT=$(echo "$RUN_INFO" | jq -r '.[0].commit.oid')
    
    echo "工作流状态: $(echo $STATUS | tr '[:lower:]' '[:upper:]')"
    echo "结论: $(echo $CONCLUSION | tr '[:lower:]' '[:upper:]')"
    echo "提交: ${RUN_COMMIT:0:7}"
    echo ""
    
    # 检查是否是我们期望的提交
    if [[ "$RUN_COMMIT" == "$COMMIT"* ]]; then
        echo "✅ 找到目标提交"
        
        # 检查是否完成
        if [[ "$STATUS" == "completed" ]]; then
            echo "✅ 工作流执行完成"
            echo ""
            
            # 获取 job 状态
            RUN_ID=$(echo "$RUN_INFO" | jq -r '.[0].databaseId')
            
            echo "================================"
echo "Job 状态"
            echo "================================"
            echo ""
            
            gh run view "$RUN_ID" 2>/dev/null || echo "无法获取 job 详细信息"
            echo ""
            
            # 检查结论
            if [[ "$CONCLUSION" == "success" ]]; then
                echo "================================"
                echo "✅ 成功！所有检查通过"
                echo "================================"
                echo ""
                exit 0
            else
                echo "================================"
                echo "❌ 失败！某些检查未通过"
                echo "================================"
                echo ""
                exit 1
            fi
        fi
    else
        echo "⏳ 还不是目标提交，继续等待..."
    fi
    
    # 如果不是最后一次尝试，等待
    if [[ $attempt -lt $MAX_ATTEMPTS ]]; then
        echo "等待 ${SLEEP_INTERVAL} 秒..."
        sleep $SLEEP_INTERVAL
        echo ""
    fi
done

echo "================================"
echo "⏱️  超时！达到最大尝试次数"
echo "================================"
echo ""
echo "请手动检查 CI 状态："
echo "  https://github.com/Joe-rq/agent-flow-lite/actions/workflows/$WORKFLOW"
echo ""
exit 1
