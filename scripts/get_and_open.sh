#!/bin/bash
# 提取并打开指定日期的 AI 听记链接

if [ $# -eq 0 ]; then
    echo "用法: ./get_and_open.sh <日期>"
    echo "示例: ./get_and_open.sh 2026-02-24"
    exit 1
fi

DATE=$1

echo "正在提取 $DATE 的链接..."
source ~/.venv/bin/activate 2>/dev/null || source .venv/bin/activate

LINK=$(python get_link_from_current_page.py "$DATE" 2>&1 | grep "找到链接:" | cut -d' ' -f2)

if [ -z "$LINK" ]; then
    echo "✗ 未找到链接"
    exit 1
fi

echo "✓ 找到链接: $LINK"
echo "正在打开..."
open "$LINK"
