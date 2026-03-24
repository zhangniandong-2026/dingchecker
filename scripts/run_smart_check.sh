#!/bin/bash
# 智能检查启动脚本 - 自动识别当前打开的钉钉页面

cd ~/dingtalk_checker

# 获取日期参数（可选）
TARGET_DATE=${1:-$(date +%Y-%m-%d)}

echo "启动智能检查..."
echo "目标日期: $TARGET_DATE"
echo ""

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 运行智能检查脚本
python3 scripts/smart_check.py "$TARGET_DATE"

# 检查是否成功
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 智能检查完成"

    # 打开最新的 PDF 报告
    LATEST_PDF=$(ls -t daily_reports/smart_report_*.pdf 2>/dev/null | head -1)
    if [ -n "$LATEST_PDF" ]; then
        echo "打开 PDF 报告: $LATEST_PDF"
        open "$LATEST_PDF"
    fi
else
    echo ""
    echo "✗ 检查失败，请查看错误信息"
    exit 1
fi
