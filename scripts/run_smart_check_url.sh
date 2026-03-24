#!/bin/bash
# 简化版启动脚本 - 直接指定 URL，不需要远程调试

# 使用方法
if [ $# -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║        钉钉智能分析 - 简化版（无需远程调试）               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "使用方法:"
    echo "  $0 <钉钉文档URL> [日期]"
    echo ""
    echo "示例:"
    echo "  $0 https://alidocs.dingtalk.com/i/nodes/xxxxx"
    echo "  $0 https://alidocs.dingtalk.com/i/nodes/xxxxx 2026-03-01"
    echo ""
    echo "提示:"
    echo "  1. 在浏览器中打开钉钉文档"
    echo "  2. 复制地址栏的 URL"
    echo "  3. 粘贴到这个命令中"
    exit 1
fi

URL="$1"
DATE="${2:-$(date +%Y-%m-%d)}"

cd ~/dingtalk_checker

echo "🚀 启动智能分析..."
echo "URL: $URL"
echo "日期: $DATE"
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 运行持久化浏览器版本
python3 scripts/smart_check_persistent.py "$URL" "$DATE"

# 打开 PDF
LATEST_PDF=$(ls -t daily_reports/smart_report_*.pdf 2>/dev/null | head -1)
if [ -n "$LATEST_PDF" ]; then
    echo ""
    echo "📄 打开报告: $LATEST_PDF"
    open "$LATEST_PDF"
fi
