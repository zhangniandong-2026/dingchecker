#!/bin/bash
# 增强版 daily check 启动器，带失败通知
# 自动生成文本报告和PDF报告

# 设置工作目录
cd /Users/zhangniandong/dingtalk_checker

# 设置代理（用于访问Google Gemini API）
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export ALL_PROXY="socks5://127.0.0.1:7890"
export NO_PROXY="localhost,127.0.0.1,::1"
# gRPC 代理（Gemini API 需要）
export GRPC_PROXY="http://127.0.0.1:7890"
export grpc_proxy="http://127.0.0.1:7890"

# 设置 Gemini API 密钥
export GEMINI_API_KEY="YOUR_API_KEY_HERE"

# 发送通知函数
send_notification() {
    local title="$1"
    local message="$2"
    osascript -e "display notification \"$message\" with title \"$title\" sound name \"Glass\""
}

# Chrome 环境预检查
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始 Chrome 环境预检查..." >> logs/daily_check.log
python3 scripts/prepare_chrome.py
if [ $? -ne 0 ]; then
    ERROR_MSG="Chrome 环境预检查失败，请检查 Chrome 是否运行和登录状态"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $ERROR_MSG" >> logs/daily_check.log
    send_notification "钉钉日会检查失败" "$ERROR_MSG"
    exit 1
fi
echo "$(date '+%Y-%m-%d %H:%M:%S') - Chrome 环境预检查通过" >> logs/daily_check.log

# 使用 caffeinate 防止脚本执行期间系统休眠
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始每日检查..." >> logs/daily_check.log

caffeinate -is python3 scripts/daily_check.py
DAILY_CHECK_EXIT=$?

if [ $DAILY_CHECK_EXIT -ne 0 ]; then
    ERROR_MSG="每日检查脚本执行失败，请查看日志"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $ERROR_MSG" >> logs/daily_check.log
    send_notification "钉钉日会检查失败" "$ERROR_MSG"
    exit 1
fi

# 记录执行日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - 文本报告生成完成" >> logs/daily_check.log

# 生成PDF报告
TODAY=$(date '+%Y-%m-%d')
REPORT_FILE="daily_reports/report_${TODAY}.txt"
PDF_FILE="daily_reports/report_${TODAY}.pdf"

if [ -f "$REPORT_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始生成PDF报告..." >> logs/daily_check.log
    python3 scripts/generate_pdf_report.py "$REPORT_FILE" "$PDF_FILE" 2>&1 >> logs/daily_check.log
    if [ $? -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - PDF报告生成完成" >> logs/daily_check.log

        # 检查成功提取的业务单元数量
        SUCCESS_COUNT=$(grep "成功提取:" "$REPORT_FILE" | head -1 | grep -oE '[0-9]+' | head -1)
        if [ -n "$SUCCESS_COUNT" ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
            send_notification "钉钉日会检查完成" "成功提取 $SUCCESS_COUNT 个业务单元的数据"
        else
            send_notification "钉钉日会检查警告" "所有业务单元均无数据"
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - PDF报告生成失败" >> logs/daily_check.log
        send_notification "钉钉日会检查警告" "PDF报告生成失败"
    fi
else
    ERROR_MSG="文本报告不存在，跳过PDF生成"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 警告：$ERROR_MSG" >> logs/daily_check.log
    send_notification "钉钉日会检查警告" "$ERROR_MSG"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily check completed" >> logs/daily_check.log
