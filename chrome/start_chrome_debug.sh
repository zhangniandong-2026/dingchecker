#!/bin/bash
# Chrome 远程调试模式启动脚本

echo "启动 Chrome 远程调试模式..."
echo "端口: 9222"
echo "配置目录: ~/chrome_debug_profile"
echo ""
echo "⚠️  启动后请："
echo "1. 登录钉钉文档"
echo "2. 打开目标表格页面"
echo "3. 保持浏览器窗口打开（可最小化）"
echo ""

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=~/chrome_debug_profile
