#!/bin/bash
# 智能启动 Chrome 远程调试并运行钉钉检查
# 自动检测 Chrome 状态，必要时启动

DINGTALK_URL="https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
CDP_PORT=9222
PROJECT_DIR="/Users/zhangniandong/dingtalk_checker"

echo "🚀 钉钉早会检查器 - 智能启动"
echo "================================"
echo ""

# 检查 Chrome 远程调试是否在运行
check_chrome_debug() {
    curl -s http://localhost:${CDP_PORT}/json/version > /dev/null 2>&1
    return $?
}

# 启动 Chrome 远程调试
start_chrome_debug() {
    echo "🌐 Chrome 远程调试未运行，正在启动..."

    # 检查并杀死旧的 Chrome 调试进程
    OLD_PID=$(ps aux | grep "remote-debugging-port=${CDP_PORT}" | grep -v grep | awk '{print $2}')
    if [ -n "$OLD_PID" ]; then
        echo "   清理旧的 Chrome 进程 (PID: ${OLD_PID})..."
        kill -9 $OLD_PID 2>/dev/null
        sleep 2
    fi

    # 启动新的 Chrome 远程调试
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=${CDP_PORT} \
        --user-data-dir="${PROJECT_DIR}/chrome/chrome_debug_profile" \
        --disable-extensions \
        --no-first-run \
        "${DINGTALK_URL}" \
        > /dev/null 2>&1 &

    CHROME_PID=$!
    echo "   ✅ Chrome 已启动 (PID: ${CHROME_PID})"

    # 等待 Chrome 就绪
    echo "   等待 Chrome 启动..."
    for i in {1..10}; do
        sleep 1
        if check_chrome_debug; then
            echo "   ✅ Chrome 远程调试已就绪（端口 ${CDP_PORT}）"
            return 0
        fi
    done

    echo "   ❌ Chrome 启动超时"
    return 1
}

# 打开钉钉表格页面
open_dingtalk_page() {
    echo "📄 正在打开钉钉表格页面..."

    # 使用 AppleScript 在 Chrome 中打开新标签页
    osascript <<EOF
        tell application "Google Chrome"
            activate
            tell window 1
                set URL of active tab to "${DINGTALK_URL}"
            end tell
        end tell
EOF

    sleep 3
    echo "   ✅ 页面已打开"
}

# 主流程
main() {
    cd "${PROJECT_DIR}"

    # 步骤 1：检查 Chrome 状态
    if check_chrome_debug; then
        echo "✅ Chrome 远程调试已在运行"
        echo ""

        # 询问是否需要打开钉钉页面
        echo "💡 提示：如果钉钉表格页面未打开，建议手动在 Chrome 中访问："
        echo "   ${DINGTALK_URL}"
        echo ""
    else
        # 启动 Chrome
        if ! start_chrome_debug; then
            echo ""
            echo "❌ Chrome 启动失败，请手动运行："
            echo "   bash ${PROJECT_DIR}/chrome/start_chrome_debug.sh"
            exit 1
        fi

        echo ""
        echo "⏳ 等待10秒让页面加载完成..."
        sleep 10

        echo ""
        echo "📌 请在打开的 Chrome 窗口中："
        echo "   1. 检查是否已登录钉钉"
        echo "   2. 确认表格页面已打开"
        echo ""
        read -p "准备好后按回车继续..." dummy
    fi

    # 步骤 2：运行检查
    echo ""
    echo "🔍 开始检查各业务单元..."
    echo "================================"
    echo ""

    bash scripts/run_daily_check.sh

    # 步骤 3：显示结果
    echo ""
    echo "================================"
    echo "✅ 检查完成！"
    echo ""

    TODAY=$(date '+%Y-%m-%d')
    PDF_FILE="${PROJECT_DIR}/daily_reports/report_${TODAY}.pdf"
    TXT_FILE="${PROJECT_DIR}/daily_reports/report_${TODAY}.txt"

    if [ -f "$PDF_FILE" ]; then
        echo "📊 报告已生成："
        echo "   PDF: ${PDF_FILE}"
        echo "   文本: ${TXT_FILE}"
        echo ""
        echo "💡 使用以下命令查看："
        echo "   open ~/dingtalk_checker/daily_reports/report_${TODAY}.pdf"
    else
        echo "⚠️  报告生成可能失败，请查看日志："
        echo "   tail -50 ${PROJECT_DIR}/logs/daily_check.log"
    fi

    echo ""
    echo "🌐 Chrome 保持运行，方便下次快速检查"
}

main
