#!/bin/bash
# 安装钉钉自动推送功能

REPO_DIR="/Users/zhangniandong/repos/dingchecker"
CONFIG_FILE="$REPO_DIR/config/dingtalk_webhook.json"
TEMPLATE_FILE="$REPO_DIR/config/dingtalk_webhook.json.template"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  钉钉自动推送功能安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查Python依赖
echo "【步骤1/5】检查Python依赖..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  缺少 requests 库，正在安装..."
    pip3 install requests
fi
echo "✓ Python依赖已满足"

# 2. 创建配置文件
echo ""
echo "【步骤2/5】创建配置文件..."
if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  配置文件已存在: $CONFIG_FILE"
    echo "   如需重新配置，请手动编辑该文件"
else
    cp "$TEMPLATE_FILE" "$CONFIG_FILE"
    echo "✓ 配置文件已创建: $CONFIG_FILE"
fi

# 3. 设置脚本权限
echo ""
echo "【步骤3/5】设置脚本权限..."
chmod +x "$REPO_DIR/scripts/send_to_dingtalk.py"
chmod +x "$REPO_DIR/scripts/auto_report_and_push.sh"
echo "✓ 权限已设置"

# 4. 创建日志目录
echo ""
echo "【步骤4/5】创建日志目录..."
mkdir -p "$REPO_DIR/logs"
echo "✓ 日志目录: $REPO_DIR/logs"

# 5. 配置定时任务
echo ""
echo "【步骤5/5】配置定时任务"
echo ""
echo "选择定时任务方式："
echo "  1) crontab (推荐)"
echo "  2) macOS LaunchAgent"
echo "  3) 跳过（稍后手动配置）"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "添加crontab定时任务（每天9:30）..."
        # 移除旧的配置（如果存在）
        (crontab -l 2>/dev/null | grep -v "auto_report_and_push.sh"; \
         echo "30 9 * * * $REPO_DIR/scripts/auto_report_and_push.sh >> $REPO_DIR/logs/auto_push.log 2>&1") | crontab -
        echo "✓ crontab已配置"
        echo "  查看配置: crontab -l"
        echo "  编辑配置: crontab -e"
        echo "  删除配置: crontab -e (然后删除对应行)"
        ;;
    2)
        echo ""
        echo "创建LaunchAgent配置..."
        PLIST="$HOME/Library/LaunchAgents/com.dingchecker.autopush.plist"
        cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dingchecker.autopush</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$REPO_DIR/scripts/auto_report_and_push.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$REPO_DIR/logs/auto_push.log</string>
    <key>StandardErrorPath</key>
    <string>$REPO_DIR/logs/auto_push_error.log</string>
</dict>
</plist>
EOF
        launchctl load "$PLIST" 2>/dev/null || true
        echo "✓ LaunchAgent已配置并加载"
        echo "  配置文件: $PLIST"
        echo "  查看状态: launchctl list | grep dingchecker"
        echo "  卸载: launchctl unload $PLIST"
        ;;
    *)
        echo "跳过定时任务配置"
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 安装完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚠️  重要：配置钉钉机器人"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "后续步骤："
echo ""
echo "1. 在钉钉群中添加自定义机器人："
echo "   - 打开钉钉群"
echo "   - 点击群设置 → 智能群助手 → 添加机器人"
echo "   - 选择「自定义」机器人"
echo "   - 安全设置选择「加签」（推荐）或「关键词」"
echo "   - 复制 Webhook URL 和加签密钥（secret）"
echo ""
echo "2. 编辑配置文件："
echo "   vim $CONFIG_FILE"
echo ""
echo "   替换以下字段："
echo "   - webhook_url: 粘贴机器人的 Webhook URL"
echo "   - secret: 粘贴加签密钥（如果使用了加签）"
echo ""
echo "3. 测试推送："
echo "   python3 $REPO_DIR/scripts/send_to_dingtalk.py \\"
echo "     --webhook \"你的webhook_url\" \\"
echo "     --secret \"你的secret\" \\"
echo "     --test"
echo ""
echo "4. 手动测试完整流程："
echo "   bash $REPO_DIR/scripts/auto_report_and_push.sh"
echo ""
echo "5. 等待定时任务自动执行（每天9:30）"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
