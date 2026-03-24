#!/bin/bash
# 环境检查脚本

echo "========================================="
echo "钉钉AI听记自动检查 - 环境验证"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success=0
warnings=0
errors=0

# 检查Python虚拟环境
echo "1. 检查 Python 虚拟环境..."
if [ -d ~/.venv ]; then
    echo -e "   ${GREEN}✓${NC} 虚拟环境存在"
    ((success++))

    # 检查playwright
    if source ~/.venv/bin/activate && python -c "import playwright" 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} playwright 已安装"
        ((success++))
    else
        echo -e "   ${RED}✗${NC} playwright 未安装"
        echo "      安装命令: source .venv/bin/activate && pip install playwright"
        ((errors++))
    fi
else
    echo -e "   ${RED}✗${NC} 虚拟环境不存在"
    echo "      创建命令: python3 -m venv .venv"
    ((errors++))
fi

echo ""

# 检查必要脚本文件
echo "2. 检查脚本文件..."
scripts=(
    "daily_check.py"
    "get_content.py"
    "get_link_from_current_page.py"
    "run_daily_check.sh"
    "install_schedule.sh"
    "start_chrome_debug.sh"
)

for script in "${scripts[@]}"; do
    if [ -f ~/"$script" ]; then
        echo -e "   ${GREEN}✓${NC} $script"
        ((success++))
    else
        echo -e "   ${RED}✗${NC} $script 缺失"
        ((errors++))
    fi
done

echo ""

# 检查Chrome是否安装
echo "3. 检查 Google Chrome..."
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo -e "   ${GREEN}✓${NC} Chrome 已安装"
    ((success++))
else
    echo -e "   ${RED}✗${NC} Chrome 未安装"
    echo "      请安装 Google Chrome"
    ((errors++))
fi

echo ""

# 检查Chrome远程调试是否运行
echo "4. 检查 Chrome 远程调试模式..."
if lsof -i :9222 >/dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Chrome 远程调试正在运行 (端口 9222)"
    ((success++))
else
    echo -e "   ${YELLOW}⚠${NC} Chrome 远程调试未运行"
    echo "      启动命令: ./start_chrome_debug.sh"
    ((warnings++))
fi

echo ""

# 检查报告目录
echo "5. 检查报告目录..."
if [ -d ~/daily_reports ]; then
    echo -e "   ${GREEN}✓${NC} 报告目录存在"
    report_count=$(ls -1 ~/daily_reports/report_*.txt 2>/dev/null | wc -l)
    echo "      已有 $report_count 个报告文件"
    ((success++))
else
    echo -e "   ${YELLOW}⚠${NC} 报告目录不存在"
    echo "      创建命令: mkdir -p ~/daily_reports"
    ((warnings++))
fi

echo ""

# 检查定时任务
echo "6. 检查定时任务..."
if launchctl list | grep -q "com.dingtalk.dailycheck"; then
    echo -e "   ${GREEN}✓${NC} 定时任务已加载"
    ((success++))
else
    echo -e "   ${YELLOW}⚠${NC} 定时任务未安装"
    echo "      安装命令: ./install_schedule.sh"
    ((warnings++))
fi

echo ""

# 检查Chrome自启动
echo "7. 检查 Chrome 自启动..."
if launchctl list | grep -q "com.chrome.debugmode"; then
    echo -e "   ${GREEN}✓${NC} Chrome 自启动已配置"
    ((success++))
else
    echo -e "   ${YELLOW}⚠${NC} Chrome 自启动未配置（可选）"
    echo "      安装命令: cp ~/com.chrome.debugmode.plist ~/Library/LaunchAgents/"
    echo "               launchctl load ~/Library/LaunchAgents/com.chrome.debugmode.plist"
    ((warnings++))
fi

echo ""
echo "========================================="
echo "检查结果"
echo "========================================="
echo -e "${GREEN}成功:${NC} $success 项"
echo -e "${YELLOW}警告:${NC} $warnings 项"
echo -e "${RED}错误:${NC} $errors 项"
echo ""

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ 环境完全就绪！${NC}"
    echo ""
    echo "可以执行："
    echo "  - 手动测试: ./run_daily_check.sh"
    echo "  - 查看日志: tail -f ~/daily_check.log"
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}⚠ 环境基本就绪，但有一些建议优化${NC}"
    echo ""
    echo "建议操作："
    if ! lsof -i :9222 >/dev/null 2>&1; then
        echo "  - 启动Chrome: ./start_chrome_debug.sh"
    fi
    if ! launchctl list | grep -q "com.dingtalk.dailycheck"; then
        echo "  - 安装定时任务: ./install_schedule.sh"
    fi
else
    echo -e "${RED}✗ 环境存在问题，请先解决错误${NC}"
fi

echo ""
