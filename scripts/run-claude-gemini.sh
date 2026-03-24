#!/bin/bash

# --- 用户配置区 ---
GEMINI_KEY="YOUR_API_KEY_HERE"
CLASH_PORT=7890 
ROUTER_PORT=4141

# --- 模型定义 ---
# 1) Gemini 3 Pro: 逻辑最强，适合复杂 B2B 规划
# 2) Gemini 3 Flash: 极速响应，适合简单代码修改
# 3) Gemini 1.5 Pro: 备用经典模型
options=("gemini-3-pro" "gemini-3-flash" "gemini-1.5-pro" "退出")

# --- 1. 交互式模型选择 ---
echo "------------------------------------------------"
echo "请选择本次要使用的 Gemini 模型 (输入数字):"
PS3="选择模型序号: "

select opt in "${options[@]}"
do
    case $opt in
        "gemini-3-pro")
            MODEL_NAME="gemini-3-pro"
            break
            ;;
        "gemini-3-flash")
            MODEL_NAME="gemini-3-flash"
            break
            ;;
        "gemini-1.5-pro")
            MODEL_NAME="gemini-1.5-pro"
            break
            ;;
        "退出")
            echo "已取消启动。"
            exit 0
            ;;
        *) echo "无效选项，请重新选择 $REPLY";;
    esac
done

# --- 2. 注入终端代理 (适配 Clash) ---
export http_proxy=http://127.0.0.1:$CLASH_PORT
export https_proxy=http://127.0.0.1:$CLASH_PORT
export ALL_PROXY=socks5://127.0.0.1:$CLASH_PORT

# --- 3. 启动转发网关 ---
if ! command -v ccr &> /dev/null; then
    echo "⚠️  正在安装 claude-code-router..."
    npm install -g claude-code-router
fi

echo "✨ 正在启动 $MODEL_NAME 网关..."
export GEMINI_API_KEY="$GEMINI_KEY"
ccr start --model "$MODEL_NAME" --port $ROUTER_PORT > /dev/null 2>&1 &
CCR_PID=$!

sleep 1.5 # 等待网关预热

# --- 4. 启动 Claude Code ---
export ANTHROPIC_BASE_URL="http://127.0.0.1:$ROUTER_PORT"
export ANTHROPIC_AUTH_TOKEN="local-session"

echo "🤖 Claude Code 启动成功 [模型: $MODEL_NAME]"
echo "提示: 输入 /exit 退出 Claude，脚本将自动关闭后台进程。"
echo "------------------------------------------------"
claude

# --- 5. 清理 ---
kill $CCR_PID 2>/dev/null
echo "🧹 后台网关已关闭。"
