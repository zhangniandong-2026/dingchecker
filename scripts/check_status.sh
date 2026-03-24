#!/bin/bash
# 检查自动化系统状态

echo "========================================================================"
echo "钉钉日会自动化系统 - 状态检查"
echo "========================================================================"
echo ""

# 1. 检查 Chrome 调试进程
echo "1️⃣  Chrome 调试进程："
if pgrep -f "remote-debugging-port=9222" > /dev/null; then
    echo "   ✅ 运行中"
    CHROME_PID=$(pgrep -f "remote-debugging-port=9222" | head -1)
    echo "   PID: $CHROME_PID"
else
    echo "   ❌ 未运行"
    echo "   💡 启动: bash ~/dingtalk_checker/chrome/start_chrome_debug.sh"
fi
echo ""

# 2. 检查定时任务
echo "2️⃣  定时任务："
if launchctl list | grep "com.dingtalk.dailycheck" > /dev/null; then
    echo "   ✅ 已加载"
    STATUS=$(launchctl list | grep "com.dingtalk.dailycheck")
    echo "   $STATUS"
else
    echo "   ❌ 未加载"
    echo "   💡 加载: launchctl load ~/Library/LaunchAgents/com.dingtalk.dailycheck.plist"
fi
echo ""

# 3. 检查最近的报告
echo "3️⃣  最近的报告："
cd ~/dingtalk_checker
if [ -d "daily_reports" ]; then
    LATEST_TXT=$(ls -t daily_reports/report_*.txt 2>/dev/null | head -1)
    LATEST_PDF=$(ls -t daily_reports/report_*.pdf 2>/dev/null | head -1)

    if [ -n "$LATEST_TXT" ]; then
        REPORT_DATE=$(basename "$LATEST_TXT" | grep -oE '202[0-9]-[0-9]{2}-[0-9]{2}')
        REPORT_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$LATEST_TXT")
        echo "   📄 最新报告: $REPORT_DATE"
        echo "   🕐 生成时间: $REPORT_TIME"

        # 读取成功提取数量
        SUCCESS=$(grep "成功提取:" "$LATEST_TXT" | head -1)
        echo "   $SUCCESS"
    else
        echo "   ⚠️  没有找到报告"
    fi
else
    echo "   ❌ 报告目录不存在"
fi
echo ""

# 4. 检查最近的日志
echo "4️⃣  最近的执行日志："
if [ -f "logs/daily_check.log" ]; then
    echo "   最后5次执行："
    tail -10 logs/daily_check.log | grep "Daily check completed" | tail -5

    # 检查是否有错误
    LAST_ERROR=$(tail -50 logs/daily_check.log | grep "失败\|错误\|Error" | tail -1)
    if [ -n "$LAST_ERROR" ]; then
        echo ""
        echo "   ⚠️  最近的错误："
        echo "   $LAST_ERROR"
    fi
else
    echo "   ⚠️  日志文件不存在"
fi
echo ""

# 5. 检查今天是否已执行
echo "5️⃣  今天的执行状态："
TODAY=$(date '+%Y-%m-%d')
if grep -q "$TODAY.*Daily check completed" logs/daily_check.log 2>/dev/null; then
    EXEC_COUNT=$(grep "$TODAY.*Daily check completed" logs/daily_check.log | wc -l | tr -d ' ')
    echo "   ✅ 今天已执行 $EXEC_COUNT 次"
    grep "$TODAY.*Daily check completed" logs/daily_check.log | tail -3
else
    echo "   ⚠️  今天尚未执行"

    # 检查当前时间
    CURRENT_HOUR=$(date '+%H')
    if [ "$CURRENT_HOUR" -lt 10 ]; then
        echo "   💡 定时任务将在 10:00 执行"
    else
        echo "   ⚠️  已过执行时间，请检查定时任务或手动运行"
    fi
fi
echo ""

# 6. 下次执行时间
echo "6️⃣  下次自动执行："
TOMORROW=$(date -v+1d '+%Y-%m-%d' 2>/dev/null || date -d "tomorrow" '+%Y-%m-%d')
echo "   📅 $TOMORROW 10:00"
echo ""

echo "========================================================================"
echo "💡 手动运行: bash ~/dingtalk_checker/scripts/run_daily_check.sh"
echo "📊 查看报告: open ~/dingtalk_checker/daily_reports/"
echo "========================================================================"
