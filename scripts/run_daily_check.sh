#!/bin/bash
# 每日检查脚本启动器（增强版）
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

# 设置 Gemini API 密钥 - 请在环境变量中配置或在此处设置
# export GEMINI_API_KEY="your_api_key_here"
if [ -z "$GEMINI_API_KEY" ]; then
    echo "警告: GEMINI_API_KEY 未设置，AI分析将被跳过"
fi

# 网络连接检查
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始网络连接检查..." >> logs/daily_check.log
bash scripts/check_network.sh >> logs/daily_check.log 2>&1
if [ $? -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 网络连接检查失败，终止执行" >> logs/daily_check.log
    exit 1
fi

# Chrome 环境预检查
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始 Chrome 环境预检查..." >> logs/daily_check.log
python3 scripts/prepare_chrome.py
if [ $? -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Chrome 环境预检查失败，终止执行" >> logs/daily_check.log
    exit 1
fi
echo "$(date '+%Y-%m-%d %H:%M:%S') - Chrome 环境预检查通过" >> logs/daily_check.log

# 使用 caffeinate 防止脚本执行期间系统休眠
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始每日检查..." >> logs/daily_check.log

caffeinate -is python3 scripts/daily_check.py

# 记录执行日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - 文本报告生成完成" >> logs/daily_check.log

# 生成PDF报告
TODAY=$(date '+%Y-%m-%d')
REPORT_FILE="daily_reports/report_${TODAY}.txt"
PDF_FILE="daily_reports/report_${TODAY}.pdf"

if [ -f "$REPORT_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始生成PDF报告..." >> logs/daily_check.log
    python3 scripts/generate_pdf_report.py "$REPORT_FILE" "$PDF_FILE" 2>&1 >> logs/daily_check.log
    echo "$(date '+%Y-%m-%d %H:%M:%S') - PDF报告生成完成" >> logs/daily_check.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 警告：文本报告不存在，跳过PDF生成" >> logs/daily_check.log
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily check completed" >> logs/daily_check.log
