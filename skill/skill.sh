#!/bin/bash

#############################################
# DingTalk Daily Check Skill - Simplified
# 固定URL版本，支持交互式单元选择
#############################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$HOME/repos/dingcheck"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
REPORTS_DIR="$PROJECT_ROOT/data/daily_reports"
CONFIG_DIR="$PROJECT_ROOT/config"
CONFIG_FILE="$CONFIG_DIR/business_units.txt"
CHROME_SCRIPT="$PROJECT_ROOT/chrome/start_chrome_debug.sh"

# Skill config paths
SKILL_DIR="$PROJECT_ROOT/skill"
SKILL_CONFIG="$SKILL_DIR/config.sh"

# 固定URL配置
DINGTALK_URL="https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm?iframeQuery=applicationId%3DgZkvecHBhQ7QSM6R8dDPL%26entrance%3Ddata"

#############################################
# Configuration Management
#############################################

load_api_key() {
    # 优先级：环境变量 > 配置文件 > 提示配置

    # 1. 检查环境变量
    if [[ -n "${GEMINI_API_KEY:-}" ]]; then
        return 0
    fi

    # 2. 检查配置文件
    if [[ -f "$SKILL_CONFIG" ]]; then
        source "$SKILL_CONFIG"
        if [[ -n "${GEMINI_API_KEY:-}" ]]; then
            return 0
        fi
    fi

    # 3. 提示用户配置
    print_warning "⚠️  未找到 Gemini API Key"
    echo ""
    print_info "💡 配置方式（三选一）："
    echo ""
    echo "方式1: 设置环境变量（推荐，临时有效）"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    echo "方式2: 创建配置文件（持久化）"
    echo "  echo \"export GEMINI_API_KEY='your-api-key-here'\" > $SKILL_CONFIG"
    echo ""
    echo "方式3: 添加到 ~/.zshrc 或 ~/.bashrc（全局有效）"
    echo "  echo \"export GEMINI_API_KEY='your-api-key-here'\" >> ~/.zshrc"
    echo ""
    print_info "📖 获取 API Key: https://aistudio.google.com/app/apikey"
    echo ""

    read -p "是否现在配置？(y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入您的 Gemini API Key: " user_api_key

        if [[ -n "$user_api_key" ]]; then
            # 保存到配置文件
            mkdir -p "$SKILL_DIR"
            echo "# Gemini API Key for ding-check skill" > "$SKILL_CONFIG"
            echo "export GEMINI_API_KEY='$user_api_key'" >> "$SKILL_CONFIG"
            chmod 600 "$SKILL_CONFIG"  # 设置为仅用户可读写

            export GEMINI_API_KEY="$user_api_key"
            print_success "✓ API Key 已保存到 $SKILL_CONFIG"
            echo ""
            return 0
        else
            print_error "❌ API Key 不能为空"
            return 1
        fi
    else
        print_warning "⚠️  跳过配置，将不会进行 AI 分析"
        return 1
    fi
}

#############################################
# Helper Functions
#############################################

print_info() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

#############################################
# Chrome Management
#############################################

ensure_chrome_debug() {
    if ! pgrep -f "remote-debugging-port=9222" > /dev/null; then
        print_info "🚀 启动Chrome调试模式..."
        bash "$CHROME_SCRIPT" &
        sleep 5

        if ! pgrep -f "remote-debugging-port=9222" > /dev/null; then
            print_error "❌ Chrome启动失败"
            exit 1
        fi
        print_success "✓ Chrome已启动"
    else
        print_success "✓ Chrome调试模式运行中"
    fi
}

open_dingtalk_url() {
    print_info "🔗 正在打开钉钉文档..."
    python3 << EOF
import asyncio
import sys
from playwright.async_api import async_playwright

async def open_url():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("$DINGTALK_URL", wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            print("✓ 页面已打开")
    except Exception as e:
        print(f"✗ 打开页面失败: {e}", file=sys.stderr)
        sys.exit(1)

asyncio.run(open_url())
EOF

    if [ $? -ne 0 ]; then
        print_error "❌ 页面打开失败"
        exit 1
    fi
}

#############################################
# Unit Selection
#############################################

select_units_interactive() {
    # 临时禁用unbound variable检查，因为中文字符串在某些bash版本中有问题
    set +u

    print_info "🔍 选择要检查的业务单元" >&2
    echo "" >&2

    # 读取配置文件，解析战队和单元（不使用关联数组，兼容Bash 3.x）
    local all_units=""
    local theaters=""
    local theater_names=""
    local current_theater=""
    local current_theater_units=""
    local theater_count=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        # 去除首尾空白
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        # 跳过空行
        if [[ -z "$line" ]]; then
            continue
        fi

        if [[ "$line" =~ ^#.* ]]; then
            # 保存上一个战队的数据
            if [[ -n "$current_theater" ]]; then
                theaters="$theaters|$current_theater_units"
                theater_names="$theater_names|$current_theater"
                theater_count=$((theater_count + 1))
            fi

            # 战队标题（注释行）
            theater=$(echo "$line" | sed 's/^#[[:space:]]*//')
            # 过滤掉文件头部的说明行
            if [[ "$theater" != "业务单元配置文件"* ]] && \
               [[ "$theater" != "每行"* ]] && \
               [[ "$theater" != "单元名称"* ]] && \
               [[ -n "$theater" ]]; then
                current_theater="$theater"
                current_theater_units=""
            fi
        else
            # 业务单元
            if [[ -z "$all_units" ]]; then
                all_units="$line"
            else
                all_units="$all_units,$line"
            fi

            if [[ -n "$current_theater" ]]; then
                if [[ -z "$current_theater_units" ]]; then
                    current_theater_units="$line"
                else
                    current_theater_units="$current_theater_units,$line"
                fi
            fi
        fi
    done < "$CONFIG_FILE"

    # 保存最后一个战队
    if [[ -n "$current_theater" ]]; then
        theaters="$theaters|$current_theater_units"
        theater_names="$theater_names|$current_theater"
        theater_count=$((theater_count + 1))
    fi

    # 去除开头的|
    theaters=$(echo "$theaters" | sed 's/^|//')
    theater_names=$(echo "$theater_names" | sed 's/^|//')

    # 计算总单元数
    local unit_count=$(echo "$all_units" | tr ',' '\n' | wc -l | tr -d ' ')

    # 显示选项（输出到stderr）
    echo "[1] 全部检查（${unit_count}个单元）" >&2
    echo "" >&2
    echo "按战队分组：" >&2

    # 显示战队选项
    local option_num=2
    IFS='|' read -ra THEATER_NAMES <<< "$theater_names"
    IFS='|' read -ra THEATERS <<< "$theaters"

    for i in "${!THEATER_NAMES[@]}"; do
        local tname="${THEATER_NAMES[$i]}"
        local tunits="${THEATERS[$i]}"
        local tcount=$(echo "$tunits" | tr ',' '\n' | wc -l | tr -d ' ')
        echo "[$option_num] $tname（$tcount个单元）" >&2
        option_num=$((option_num + 1))
    done

    echo "" >&2
    echo "单个业务单元：" >&2
    IFS=',' read -ra UNITS <<< "$all_units"
    for unit in "${UNITS[@]}"; do
        echo "  • $unit" >&2
    done

    echo "" >&2
    echo "请选择：" >&2
    echo "  - 输入数字选择快捷选项（如：1 表示全部，2 表示第一个战队）" >&2
    echo "  - 输入单元名称（逗号分隔）选择特定单元" >&2
    echo "  - 按 Enter 检查全部" >&2
    echo "" >&2
    read -p "您的选择: " selection

    # 解析选择
    local selected_units=""

    if [[ -z "$selection" ]]; then
        # 默认全部
        selected_units="$all_units"
    elif [[ "$selection" =~ ^[0-9]+$ ]]; then
        # 数字选项
        if [[ "$selection" == "1" ]]; then
            selected_units="$all_units"
        else
            # 战队选项 (2, 3, 4, ...)
            local theater_idx=$((selection - 2))
            if [[ $theater_idx -ge 0 ]] && [[ $theater_idx -lt ${#THEATERS[@]} ]]; then
                selected_units="${THEATERS[$theater_idx]}"
            else
                print_error "❌ 无效选项" >&2
                set -u
                exit 1
            fi
        fi
    else
        # 直接输入单元名称
        selected_units="$selection"
    fi

    # 恢复unbound variable检查
    set -u

    # 只输出选择结果到stdout
    echo "$selected_units"
}

#############################################
# Core Check Function
#############################################

run_daily_check() {
    local date="$1"
    local selected_units="$2"

    print_info "🚀 开始检查..."
    print_info "📅 日期: $date"

    # 计算单元数量
    local unit_count=$(echo "$selected_units" | tr ',' '\n' | wc -l | tr -d ' ')
    print_info "📋 单元数: $unit_count"
    echo ""

    cd "$PROJECT_ROOT"

    # 配置备份和恢复函数
    local config_backup=""

    cleanup_config() {
        if [[ -n "$config_backup" ]] && [[ -f "$config_backup" ]]; then
            mv "$config_backup" "$CONFIG_FILE"
            print_info "✓ 已恢复配置文件"
        fi
    }

    # 设置trap确保配置恢复
    trap cleanup_config EXIT INT TERM

    # 备份并创建临时配置
    if [[ -n "$selected_units" ]] && [[ "$selected_units" != "all" ]]; then
        config_backup="$CONFIG_FILE.bak.$$"
        cp "$CONFIG_FILE" "$config_backup"

        # 创建临时配置（只包含选择的单元）
        echo "# 临时配置 - skill 生成 at $(date)" > "$CONFIG_FILE"
        IFS=',' read -ra units <<< "$selected_units"
        for unit in "${units[@]}"; do
            unit=$(echo "$unit" | xargs)  # trim whitespace
            echo "$unit" >> "$CONFIG_FILE"
        done
        print_info "✓ 已创建临时配置"
    fi

    # 加载 API Key
    if ! load_api_key; then
        print_warning "⚠️  未配置 API Key，将跳过 AI 分析"
        echo ""
    fi

    # 检测是否需要设置代理
    # 如果本地7890端口有代理服务则使用，否则直连（适用于软路由场景）
    if netstat -an 2>/dev/null | grep -q "7890.*LISTEN" || lsof -i :7890 2>/dev/null | grep -q LISTEN; then
        # 本地代理可用
        export HTTP_PROXY="http://127.0.0.1:7890"
        export HTTPS_PROXY="http://127.0.0.1:7890"
        export ALL_PROXY="socks5://127.0.0.1:7890"
        export NO_PROXY="localhost,127.0.0.1,::1"
        export GRPC_PROXY="http://127.0.0.1:7890"
        export grpc_proxy="http://127.0.0.1:7890"
        print_info "🔌 使用本地代理: 127.0.0.1:7890" >&2
    else
        # 软路由或全局代理，清除可能存在的代理设置
        unset HTTP_PROXY HTTPS_PROXY ALL_PROXY GRPC_PROXY grpc_proxy
        export NO_PROXY="localhost,127.0.0.1,::1"
        print_info "🌐 使用直连模式（软路由）" >&2
    fi

    # 运行检查
    print_info "🔄 正在提取数据..."
    if ! python3 "$SCRIPTS_DIR/daily_check.py" "$date"; then
        print_error "❌ 检查过程出错，请查看日志"
        cleanup_config
        trap - EXIT INT TERM
        exit 1
    fi

    # 恢复配置
    cleanup_config
    trap - EXIT INT TERM

    echo ""

    # 生成PDF和HTML报告
    local report_file="$REPORTS_DIR/report_${date}.txt"
    local pdf_file="$REPORTS_DIR/report_${date}.pdf"
    local html_file="$REPORTS_DIR/report_${date}.html"

    if [ -f "$report_file" ]; then
        print_info "📊 正在生成可视化报告..."

        # 生成PDF
        if python3 "$SCRIPTS_DIR/generate_pdf_report.py" "$report_file" "$pdf_file" 2>/dev/null; then
            print_success "✓ PDF报告生成成功"
        else
            print_warning "⚠️  PDF生成失败（文本报告仍可用）"
        fi

        # 生成HTML
        if python3 "$SCRIPTS_DIR/generate_html_report.py" "$report_file" "$html_file" 2>/dev/null; then
            print_success "✓ HTML可视化报告生成成功"
        else
            print_warning "⚠️  HTML生成失败（文本报告仍可用）"
        fi
    fi

    # 显示结果
    echo ""
    if [ -f "$report_file" ]; then
        print_success "✅ 检查完成！"
        echo ""
        print_info "📄 文本报告: $report_file"

        if [ -f "$html_file" ]; then
            print_info "🌐 HTML可视化报告: $html_file"
            print_info "🔓 正在打开HTML报告..."
            open "$html_file"
        fi

        if [ -f "$pdf_file" ]; then
            print_info "📊 PDF报告: $pdf_file"
        fi

        echo ""
        print_info "📊 检查摘要:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        head -20 "$report_file"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        print_warning "⚠️  未找到 $date 的数据"
        echo ""
        print_info "💡 可能的原因："
        echo "   1. 今天还没有数据"
        echo "   2. 页面中没有识别到有效的业务单元"
        echo "   3. 数据提取失败"
        echo ""
        show_available_dates
    fi
}

#############################################
# View/Search/List Functions
#############################################

view_report() {
    local date_input="${1:-today}"
    local date

    # Parse date
    case "$date_input" in
        today|今天)
            date=$(date +%Y-%m-%d)
            ;;
        yesterday|昨天)
            date=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "1 day ago" +%Y-%m-%d)
            ;;
        *)
            date="$date_input"
            ;;
    esac

    print_info "📄 查看报告: $date"
    echo ""

    local report_file="$REPORTS_DIR/report_${date}.txt"
    local pdf_file="$REPORTS_DIR/report_${date}.pdf"
    local html_file="$REPORTS_DIR/report_${date}.html"

    if [ -f "$html_file" ]; then
        print_success "✓ 找到HTML报告"
        print_info "🌐 打开: $html_file"
        open "$html_file"
        echo ""
    fi

    if [ -f "$pdf_file" ]; then
        print_success "✓ 找到PDF报告"
        print_info "📊 打开: $pdf_file"
        open "$pdf_file"
        echo ""
    fi

    if [ -f "$report_file" ]; then
        print_success "✓ 找到文本报告"
        echo ""
        cat "$report_file"
        echo ""
    else
        print_warning "⚠️  未找到 $date 的报告"
        echo ""
        show_available_dates
        exit 1
    fi
}

search_reports() {
    local keyword="$1"

    if [ -z "$keyword" ]; then
        print_error "❌ 请提供搜索关键词"
        echo ""
        echo "用法: /ding-check search [关键词]"
        exit 1
    fi

    print_info "🔍 搜索关键词: $keyword"
    echo ""

    local found=0

    # Search in all reports
    for report in "$REPORTS_DIR"/report_*.txt; do
        if [ -f "$report" ]; then
            local matches=$(grep -i "$keyword" "$report" | wc -l | tr -d ' ')
            if [ "$matches" -gt 0 ]; then
                local basename=$(basename "$report")
                local date=$(echo "$basename" | sed 's/report_\(.*\)\.txt/\1/')

                print_success "📅 $date ($matches 处匹配)"
                grep -i --color=always -B 1 -A 1 "$keyword" "$report" | head -20
                echo ""
                found=1
            fi
        fi
    done

    if [ $found -eq 0 ]; then
        print_warning "⚠️  未找到包含 '$keyword' 的报告"
    fi
}

list_reports() {
    print_info "📋 历史报告列表"
    echo ""

    local count=0

    # List all reports, sorted by date (newest first)
    for report in $(ls -t "$REPORTS_DIR"/report_*.txt 2>/dev/null); do
        if [ -f "$report" ]; then
            local basename=$(basename "$report")
            local date=$(echo "$basename" | sed 's/report_\(.*\)\.txt/\1/')
            local pdf_file="$REPORTS_DIR/report_${date}.pdf"
            local html_file="$REPORTS_DIR/report_${date}.html"

            local file_info="📄 TXT"
            if [ -f "$pdf_file" ]; then
                file_info="📄 TXT + 📊 PDF"
            fi
            if [ -f "$html_file" ]; then
                file_info="$file_info + 🌐 HTML"
            fi

            # Get first line (title) from report
            local title=$(head -1 "$report" | sed 's/^=* *//' | sed 's/ *=*$//')

            echo "  $date  $file_info"
            echo "    $title"
            echo ""

            count=$((count + 1))
        fi
    done

    if [ $count -eq 0 ]; then
        print_warning "⚠️  没有找到历史报告"
        echo ""
        print_info "💡 运行检查生成报告："
        echo "   /ding-check"
    else
        print_success "✓ 共找到 $count 个报告"
        echo ""
        print_info "💡 查看报告："
        echo "   /ding-check view 2026-03-02"
        echo "   /ding-check view 昨天"
    fi
}

check_status() {
    print_info "🔧 系统状态检查"
    echo ""

    # Check dingtalk_checker directory
    if [ -d "$PROJECT_ROOT" ]; then
        print_success "✓ 项目目录: $PROJECT_ROOT"
    else
        print_error "✗ 项目目录不存在: $PROJECT_ROOT"
    fi

    # Check scripts
    if [ -f "$SCRIPTS_DIR/daily_check.py" ]; then
        print_success "✓ 检查脚本: daily_check.py"
    else
        print_error "✗ 检查脚本不存在"
    fi

    if [ -f "$SCRIPTS_DIR/generate_pdf_report.py" ]; then
        print_success "✓ PDF生成脚本"
    else
        print_error "✗ PDF生成脚本不存在"
    fi

    if [ -f "$SCRIPTS_DIR/generate_html_report.py" ]; then
        print_success "✓ HTML生成脚本"
    else
        print_error "✗ HTML生成脚本不存在"
    fi

    # Check Chrome debug mode
    if pgrep -f "remote-debugging-port=9222" > /dev/null; then
        print_success "✓ Chrome调试模式运行中"
    else
        print_warning "⚠️  Chrome调试模式未运行"
        echo "   skill会自动启动Chrome"
    fi

    # Check config file
    if [ -f "$CONFIG_FILE" ]; then
        local unit_count=$(grep -v "^#" "$CONFIG_FILE" | grep -v "^$" | wc -l | tr -d ' ')
        print_success "✓ 配置文件: $unit_count 个业务单元"
    else
        print_error "✗ 配置文件不存在"
    fi

    # Check Python dependencies
    echo ""
    print_info "📦 Python依赖:"

    python3 -c "import playwright" 2>/dev/null && print_success "✓ playwright" || print_error "✗ playwright"
    python3 -c "import pandas" 2>/dev/null && print_success "✓ pandas" || print_error "✗ pandas"
    python3 -c "import reportlab" 2>/dev/null && print_success "✓ reportlab" || print_error "✗ reportlab"

    # Check reports directory
    echo ""
    if [ -d "$REPORTS_DIR" ]; then
        local report_count=$(ls -1 "$REPORTS_DIR"/report_*.txt 2>/dev/null | wc -l | tr -d ' ')
        print_success "✓ 报告目录: $report_count 个报告"
    else
        print_warning "⚠️  报告目录不存在"
    fi

    # Show fixed URL
    echo ""
    print_info "🔗 固定URL:"
    echo "   $DINGTALK_URL"
}

show_available_dates() {
    print_info "📅 最近的报告："
    echo ""

    local found=0
    for i in {0..6}; do
        local check_date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "${i} days ago" +%Y-%m-%d)
        local report_file="$REPORTS_DIR/report_${check_date}.txt"

        if [ -f "$report_file" ]; then
            print_success "  ✓ $check_date"
            found=1
        else
            echo "    $check_date"
        fi
    done

    if [ $found -eq 1 ]; then
        echo ""
        print_info "💡 查看指定日期："
        echo "   /ding-check view 2026-03-02"
    fi
}

show_help() {
    cat << 'EOF'
🔧 DingTalk Daily Check Skill

用法:
  /ding-check                       交互式检查（今天）
  /ding-check [日期]                 交互式检查指定日期
  /ding-check view [日期]           查看报告
  /ding-check search [关键词]       搜索历史报告
  /ding-check list                  列出所有报告
  /ding-check status                检查系统状态

示例:
  # 交互式选择业务单元（今天）
  /ding-check

  # 交互式选择业务单元（指定日期）
  /ding-check 2026-03-02

  # 查看报告
  /ding-check view
  /ding-check view 昨天
  /ding-check view 2026-03-02

  # 搜索关键词
  /ding-check search 风险
  /ding-check search 未完成

  # 列出历史
  /ding-check list

  # 检查状态
  /ding-check status

特性:
  ✓ 固定URL - 自动使用配置的钉钉文档
  ✓ 自动启动 - 自动启动Chrome调试模式
  ✓ 交互式选择 - 灵活选择要检查的业务单元
  ✓ 全自动化 - 一条命令完成所有操作
EOF
}

#############################################
# Helper: Get units by theater name
#############################################

get_units_by_theater() {
    local theater_name="$1"
    set +u

    local all_units=""
    local current_theater=""
    local current_theater_units=""
    local found=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -z "$line" ]]; then
            continue
        fi

        if [[ "$line" =~ ^#.* ]]; then
            # 保存上一个战队的数据
            if [[ -n "$current_theater" ]] && [[ "$current_theater" == "$theater_name" ]]; then
                found=1
                echo "$current_theater_units"
                set -u
                return 0
            fi

            # 新战队标题
            theater=$(echo "$line" | sed 's/^#[[:space:]]*//')
            if [[ "$theater" != "业务单元配置文件"* ]] && \
               [[ "$theater" != "每行"* ]] && \
               [[ "$theater" != "单元名称"* ]] && \
               [[ -n "$theater" ]]; then
                current_theater="$theater"
                current_theater_units=""
            fi
        else
            # 业务单元
            if [[ -n "$current_theater" ]]; then
                if [[ -z "$current_theater_units" ]]; then
                    current_theater_units="$line"
                else
                    current_theater_units="$current_theater_units,$line"
                fi
            fi
        fi
    done < "$CONFIG_FILE"

    # 检查最后一个战队
    if [[ -n "$current_theater" ]] && [[ "$current_theater" == "$theater_name" ]]; then
        echo "$current_theater_units"
        set -u
        return 0
    fi

    set -u
    return 1
}

#############################################
# Main Entry Point
#############################################

main() {
    local first_arg="${1:-}"
    local date=""
    local selected_units=""

    # 子命令处理
    case "$first_arg" in
        view)
            view_report "${2:-today}"
            return
            ;;
        search)
            search_reports "$2"
            return
            ;;
        list)
            list_reports
            return
            ;;
        status)
            check_status
            return
            ;;
        help|-h|--help)
            show_help
            return
            ;;
        "")
            # 无参数 - 交互式选择
            date=$(date +%Y-%m-%d)
            ;;
        *)
            # 日期参数、战队名称或单元名称
            if [[ "$first_arg" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
                # 是日期格式
                date="$first_arg"
            else
                # 尝试作为战队名称查找
                # 检查第二个参数是否是日期
                if [[ "$2" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
                    date="$2"
                else
                    date=$(date +%Y-%m-%d)
                fi

                local theater_units=$(get_units_by_theater "$first_arg")

                if [[ -n "$theater_units" ]]; then
                    # 找到战队，使用战队下的所有单元
                    selected_units="$theater_units"
                    print_info "📋 检查战队: $first_arg"
                    local unit_count=$(echo "$selected_units" | tr ',' '\n' | wc -l | tr -d ' ')
                    echo "   包含单元数: $unit_count"
                    echo ""
                else
                    # 未找到战队，作为单元名称处理
                    selected_units="$first_arg"
                    print_info "📋 直接检查指定单元"
                    echo "   单元: $selected_units"
                    echo ""
                fi
            fi
            ;;
    esac

    # 主检查流程
    if [[ -z "$selected_units" ]]; then
        print_info "🔍 钉钉日会检查"
        echo "   日期: $date"
        echo ""
    fi

    # 1. 确保Chrome运行
    ensure_chrome_debug
    echo ""

    # 2. 打开URL
    open_dingtalk_url
    echo ""

    # 3. 如果没有指定单元，交互式选择
    if [[ -z "$selected_units" ]]; then
        selected_units=$(select_units_interactive)
        echo ""
    fi

    if [[ -z "$selected_units" ]]; then
        print_error "❌ 未选择任何单元"
        exit 1
    fi

    # 4. 运行检查
    run_daily_check "$date" "$selected_units"
}

# Run main function
main "$@"
