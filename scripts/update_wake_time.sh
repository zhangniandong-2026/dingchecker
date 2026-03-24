#!/bin/bash
# 更新 Mac 自动唤醒时间为 9:35

echo "========================================"
echo "更新 Mac 自动唤醒时间"
echo "========================================"
echo ""
echo "将设置 Mac 每天 9:35 自动唤醒（为 9:40 的定时任务做准备）"
echo ""
echo "需要管理员密码..."
echo ""

sudo pmset repeat wake MTWRFSU 09:35:00

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 设置成功！"
    echo ""
    echo "验证设置："
    pmset -g sched
    echo ""
    echo "========================================"
    echo "💡 Mac 将在每天 9:35 自动唤醒"
    echo "💡 然后在 9:40 执行钉钉日会检查"
    echo "========================================"
else
    echo ""
    echo "❌ 设置失败"
    echo ""
fi
