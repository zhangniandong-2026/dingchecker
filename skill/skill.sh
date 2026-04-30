#!/bin/bash

#############################################
# DingTalk Minutes Analysis Skill - v4.0
# 基于 dws CLI + Claude 本地分析
#############################################

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
REPORTS_DIR="$PROJECT_ROOT/data/daily_reports"
CONFIG_DIR="$PROJECT_ROOT/config"
UNIT_MAPPING="$CONFIG_DIR/unit_to_table.json"

# Obsidian vault path
VAULT_PATH="${DINGCHECK_VAULT_PATH:-$HOME/.claude/Obsidian Vault}"
VAULT_OUTPUT="$VAULT_PATH/ai-output/dingtalk-minutes"

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
# dws Management
#############################################

install_dws() {
    print_info "📦 dws 未安装，正在自动安装..."
    if curl -fsSL https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.sh | sh; then
        export PATH="$HOME/.local/bin:$PATH"
        hash -r 2>/dev/null || true
        print_success "✓ dws 安装完成"
        return 0
    fi
    print_error "❌ dws 安装失败"
    return 1
}

authenticate_dws() {
    print_info "🔐 dws 需要认证，正在打开登录..."
    if dws auth login; then
        print_success "✓ dws 认证完成"
        return 0
    fi
    print_error "❌ dws 认证失败"
    return 1
}

#############################################
# Business Unit Selection
#############################################

get_team_units() {
    case "$1" in
        政府头部战队)
            echo "媒体军工组,交通行业组,政府行业一组,政府行业二组"
            ;;
        华北东北战区)
            echo "北京非金一组,北京非金二组,北京金融分战队,东北组,华北一组,华北二组,北京商业组"
            ;;
        华东战区)
            echo "安徽组,山东组,浙江组,江苏非金组,苏皖金融组,华东通信组,上海金融一组,上海金融二组,上海政企一组,上海政企二组"
            ;;
        华中战区)
            echo "河南组,湖南组,湖北江西组"
            ;;
        金融头部战队)
            echo "金融头部战队"
            ;;
        华南战区)
            echo "南区行业分战队,南区金融分战队,深圳分战队,粤港澳分战队,福建组"
            ;;
        西南西北战区)
            echo "西南西北战区"
            ;;
        通信头部战队)
            echo "移动组,联通组"
            ;;
        能源央企头部战队)
            echo "能源组,央企组"
            ;;
        *)
            return 1
            ;;
    esac
}

get_all_teams() {
    echo "政府头部战队"
    echo "华北东北战区"
    echo "华东战区"
    echo "华中战区"
    echo "金融头部战队"
    echo "华南战区"
    echo "西南西北战区"
    echo "通信头部战队"
    echo "能源央企头部战队"
}

select_units_by_scope() {
    local scope="$1"

    # 从映射文件读取所有单元
    if [[ ! -f "$UNIT_MAPPING" ]]; then
        print_error "❌ 未找到单元映射文件: $UNIT_MAPPING"
        return 1
    fi

    local all_units
    all_units=$(python3 -c "import json; print(','.join(json.load(open('$UNIT_MAPPING')).keys()))")

    # 根据范围选择
    if [[ "$scope" == "全部" ]]; then
        echo "$all_units"
    elif get_team_units "$scope" >/dev/null 2>&1; then
        get_team_units "$scope"
    else
        # 单个业务单元
        if echo "$all_units" | tr ',' '\n' | grep -qx "$scope"; then
            echo "$scope"
        else
            print_error "❌ 未知业务单元: $scope"
            print_info "可用单元: $(echo "$all_units" | tr ',' '\n' | head -5 | paste -sd, -)..."
            return 1
        fi
    fi
}

#############################################
# Main Commands
#############################################

cmd_collect() {
    local scope="${1:-全部}"
    local date_arg="${2:-$(date +%Y-%m-%d)}"

    print_info "🔍 收集听记数据"
    print_info "   范围: $scope"
    print_info "   日期: $date_arg"
    echo ""

    # 快速路径：检查 dws 命令
    if ! command -v dws >/dev/null 2>&1; then
        install_dws || return 1
    fi

    # 选择业务单元
    local units
    units=$(select_units_by_scope "$scope") || return 1

    local unit_count
    unit_count=$(echo "$units" | tr ',' '\n' | wc -l | tr -d ' ')

    print_info "✓ 选中 $unit_count 个业务单元"
    echo ""

    # 输出文件
    local output="$REPORTS_DIR/minutes_${date_arg}.json"

    # 调用 Python 脚本
    python3 "$SCRIPTS_DIR/collect_minutes_dws.py" \
        --date "$date_arg" \
        --units "$units" \
        --mapping "$UNIT_MAPPING" \
        --output "$output"

    local rc=$?

    # 认证失败，触发登录后重试
    if [[ $rc -eq 2 ]]; then
        authenticate_dws || return 1
        python3 "$SCRIPTS_DIR/collect_minutes_dws.py" \
            --date "$date_arg" \
            --units "$units" \
            --mapping "$UNIT_MAPPING" \
            --output "$output" || return 1
    elif [[ $rc -ne 0 ]]; then
        return 1
    fi

    # 提示 Claude 分析
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "✅ 数据收集完成"
    echo ""
    print_info "📁 数据文件: $output"
    echo ""
    print_info "🤖 [CLAUDE-ANALYZE] 请生成双报告："
    echo ""
    echo "【报告1：内部存档版】"
    echo "  位置: $VAULT_OUTPUT/report_${date_arg}.md"
    echo "  内容: 预警信息 + 排名表格 + 详细评分 + 改进建议"
    echo "  特点: 紧凑，不含评分标准（用双链引用 [[meeting_guidelines_v4]]）"
    echo ""
    echo "【报告2：对外发布版】"
    echo "  位置: $REPORTS_DIR/report_${date_arg}_publish.md"
    echo "  内容: 完整报告 + 四维度评分标准 + 3段式汇报结构 + 纪律红线"
    echo "  特点: 自包含，业务单元可直接使用"
    echo ""
    echo "评分维度（总分20分）："
    echo "  1. 昨日战果 (1-5分): 是否清晰汇报昨天成果（客户名+动作+结果+数据）"
    echo "  2. 今日计划 (1-5分): 是否有明确的今日任务（客户名+动作+deadline）"
    echo "  3. 协同效率 (1-5分): 管理者是否现场响应，协同方（售前/交付）是否反馈"
    echo "  4. 点评效率 (1-5分): 管理者指导是否有力，发言时长占比是否合理（20-30%）"
    echo ""
    echo "报告结构："
    echo "  1️⃣ 预警信息（三类区分）"
    echo "     - 🔴 未开会单元（meeting_count=0 且未找到听记）"
    echo "     - 🟡 有听记但无转写（paragraph_count=0）"
    echo "     - 🟣 无访问权限（听记存在但返回 no permission）"
    echo "  2️⃣ 综合排名表格（横向比较）"
    echo "  3️⃣ 详细评分（每个单元展开）"
    echo "  4️⃣ 评分标准（仅发布版包含完整标准）"
    echo ""
    echo "参考文档: $PROJECT_ROOT/docs/meeting_guidelines_v4.md"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

cmd_view() {
    local date_arg="${1:-$(date +%Y-%m-%d)}"
    local report_file="$VAULT_OUTPUT/report_${date_arg}.md"

    if [[ -f "$report_file" ]]; then
        print_success "✓ 报告文件: $report_file"
        echo ""
        head -30 "$report_file"
        echo ""
        echo "..."
        echo ""
        print_info "💡 完整报告请在 Obsidian 中查看"
    else
        print_warning "⚠️  未找到报告: $report_file"
    fi
}

cmd_list_units() {
    if [[ ! -f "$UNIT_MAPPING" ]]; then
        print_error "❌ 未找到单元映射文件"
        return 1
    fi

    print_info "📋 可用业务单元："
    echo ""
    python3 -c "
import json
data = json.load(open('$UNIT_MAPPING'))
for i, (name, table_id) in enumerate(data.items(), 1):
    print(f'{i:2d}. {name}')
"
    echo ""
    print_info "战队/战区："
    get_all_teams | while read team; do
        echo "  • $team"
    done
}

cmd_help() {
    cat <<'EOF'
DingTalk Minutes Analysis Skill - v4.0

基于 dws CLI 和 Claude 本地分析的晨会质量评估工具

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
命令列表
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  collect <范围> [日期]   收集听记数据并触发分析
                          范围: 业务单元名 | 战队名 | 战区名 | 全部
                          日期: YYYY-MM-DD (默认今天)

  view [日期]             查看分析报告

  list-units              列出所有业务单元

  help                    显示此帮助

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
使用示例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # 分析单个业务单元今天的早会
  /ding-check collect 东北组

  # 分析整个战队昨天的早会
  /ding-check collect 政府头部战队 2026-04-29

  # 分析战区所有单元
  /ding-check collect 华北东北战区

  # 分析所有业务单元
  /ding-check collect 全部

  # 查看今天的分析报告
  /ding-check view

  # 列出所有可用业务单元
  /ding-check list-units

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
环境变量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  DINGCHECK_VAULT_PATH    Obsidian vault 路径
                          (默认: ~/.claude/Obsidian Vault)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
技术架构
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  数据源: 钉钉 AI 听记 (通过 dws CLI API)
  分析: Claude Code 本地分析
  输出: Markdown 报告 → Obsidian vault

  优势: 无需 Chrome/CDP，无需 Gemini API Key，数据完整可控

EOF
}

#############################################
# Main Entry
#############################################

main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        collect)
            cmd_collect "$@"
            ;;
        view)
            cmd_view "$@"
            ;;
        list-units)
            cmd_list_units
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "❌ 未知命令: $cmd"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

# 确保 reports 目录存在
mkdir -p "$REPORTS_DIR"
mkdir -p "$VAULT_OUTPUT"

main "$@"
