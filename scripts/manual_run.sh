#!/bin/bash
# 早会报告手动执行快捷脚本

DATE=$(date +%Y-%m-%d)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  早会报告手动执行 - $DATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 步骤1：数据采集
echo "【步骤1/2】数据采集..."
cd ~/.claude/Obsidian\ Vault
claude /ding-check collect 全部

# 等待用户确认Claude已生成报告
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  请等待Claude生成报告完成"
echo "    看到 report_${DATE}_publish.md 后按回车继续"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "按回车键继续推送到钉钉..."

# 步骤2：推送到钉钉
echo ""
echo "【步骤2/2】推送到钉钉..."
cd ~/repos/dingchecker
python3 scripts/send_to_dingtalk.py \
  --date $DATE \
  --report ~/.claude/Obsidian\ Vault/ai-output/dingtalk-minutes/report_${DATE}_publish.md

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 手动执行完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
