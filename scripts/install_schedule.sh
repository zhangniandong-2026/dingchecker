#!/bin/bash
# 定时任务一键安装脚本

echo "========================================="
echo "钉钉AI听记每日自动检查 - 定时任务安装"
echo "========================================="
echo ""

# 检查文件是否存在
if [ ! -f ~/com.dingtalk.dailycheck.plist ]; then
    echo "✗ 错误: 找不到 com.dingtalk.dailycheck.plist"
    exit 1
fi

if [ ! -f ~/run_daily_check.sh ]; then
    echo "✗ 错误: 找不到 run_daily_check.sh"
    exit 1
fi

if [ ! -f ~/daily_check.py ]; then
    echo "✗ 错误: 找不到 daily_check.py"
    exit 1
fi

# 确保启动脚本有执行权限
echo "1. 设置脚本执行权限..."
chmod +x ~/run_daily_check.sh
echo "✓ 完成"

# 创建报告目录
echo ""
echo "2. 创建报告目录..."
mkdir -p ~/daily_reports
echo "✓ 完成"

# 复制 plist 到 LaunchAgents
echo ""
echo "3. 安装定时任务配置..."
cp ~/com.dingtalk.dailycheck.plist ~/Library/LaunchAgents/
echo "✓ 完成"

# 卸载旧任务（如果存在）
echo ""
echo "4. 清理旧任务..."
launchctl unload ~/Library/LaunchAgents/com.dingtalk.dailycheck.plist 2>/dev/null
echo "✓ 完成"

# 加载新任务
echo ""
echo "5. 加载定时任务..."
launchctl load ~/Library/LaunchAgents/com.dingtalk.dailycheck.plist

if [ $? -eq 0 ]; then
    echo "✓ 完成"
else
    echo "✗ 加载失败"
    exit 1
fi

# 验证任务
echo ""
echo "6. 验证任务状态..."
if launchctl list | grep -q "com.dingtalk.dailycheck"; then
    echo "✓ 任务已成功加载"
else
    echo "✗ 任务未找到"
    exit 1
fi

echo ""
echo "========================================="
echo "安装完成！"
echo "========================================="
echo ""
echo "执行时间: 每天上午 10:00"
echo "报告目录: ~/daily_reports/"
echo ""
echo "⚠️  重要提醒："
echo "定时任务执行前，必须确保 Chrome 远程调试模式已启动！"
echo ""
echo "启动命令："
echo "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=~/chrome_debug_profile"
echo ""
echo "查看日志："
echo "  tail -f ~/daily_check.log"
echo "  tail -f ~/daily_check_stdout.log"
echo ""
echo "手动测试："
echo "  ./run_daily_check.sh"
echo ""
echo "卸载任务："
echo "  launchctl unload ~/Library/LaunchAgents/com.dingtalk.dailycheck.plist"
echo ""
