#!/bin/bash
# 早会报告完整自动化工作流

set -eo pipefail

# 配置
REPO_DIR="/Users/zhangniandong/repos/dingchecker"
VAULT_DIR="/Users/zhangniandong/.claude/Obsidian Vault"
SKILL_DIR="$REPO_DIR/skill"
SCRIPTS_DIR="$REPO_DIR/scripts"
LOG_DIR="$REPO_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日期（默认为今天，9:30 触发时早会刚结束）
TARGET_DATE="${1:-$(date +%Y-%m-%d)}"

# 日志函数
log() {
    echo "[$TARGET_DATE $(date +%H:%M:%S)] $1" | tee -a "$LOG_DIR/auto_push.log"
}

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  早会报告自动化流程开始"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 步骤1：采集早会数据
log ""
log "【步骤1/3】采集早会数据..."
cd "$REPO_DIR"

if [ ! -f "$SKILL_DIR/skill.sh" ]; then
    log "❌ skill.sh 不存在: $SKILL_DIR/skill.sh"
    exit 1
fi

# 采集全部单元数据
bash "$SKILL_DIR/skill.sh" collect 全部 "$TARGET_DATE" 2>&1 | tee -a "$LOG_DIR/auto_push.log"

if [ $? -ne 0 ]; then
    log "❌ 数据采集失败"
    exit 1
fi

log "✅ 数据采集完成"

# 步骤2：生成报告（使用 Claude CLI）
log ""
log "【步骤2/3】生成分析报告..."
REPORT_FILE="$VAULT_DIR/ai-output/dingtalk-minutes/report_${TARGET_DATE}.md"

# 切换到 vault 目录（确保 Claude 能访问 CLAUDE.md）
cd "$VAULT_DIR"

# 构建 Claude 提示
PROMPT="读取 ~/repos/dingchecker/data/daily_reports/minutes_${TARGET_DATE}.json 文件，这是${TARGET_DATE}早会的听记数据。请按照 [[meeting_guidelines_v4]] 的四维度评分标准生成分析报告，输出到 ai-output/dingtalk-minutes/report_${TARGET_DATE}.md。

报告要求：
1. Frontmatter：title/created/tags（#ai-generated #dingtalk #daily-companion）/type/summary
2. 预警信息：🔴未开会（status='未开会'）、🟡无转写（status='无转写'）、🟣权限错误（status='权限错误'）三类区分
3. 综合排名表格：包含战队/战区分组
4. 详细评分：每个单元展开，四维度评分（昨日战果、今日计划、协同效率、点评效率，总分20分）
5. 改进建议
6. 紧凑风格，评分标准用 [[meeting_guidelines_v4]] 双链引用
7. 激励机制：累计前三10次→[[朱文雷]]请客，累计后五10次→[[张建栋]]请茶

评分标准参考：~/repos/dingchecker/docs/meeting_guidelines_v4.md"

log "   调用 Claude 生成报告..."
log "   报告路径: $REPORT_FILE"

# 调用 Claude CLI（非交互模式，自动权限）
claude -p --permission-mode auto "$PROMPT" 2>&1 | tee -a "$LOG_DIR/auto_push.log"

if [ $? -ne 0 ]; then
    log "❌ 报告生成失败"
    exit 1
fi

# 验证报告文件是否生成
if [ ! -f "$REPORT_FILE" ]; then
    log "❌ 报告文件未生成: $REPORT_FILE"
    exit 1
fi

log "✅ 报告已生成: $REPORT_FILE"

# 步骤3：推送到钉钉
log ""
log "【步骤3/3】推送到钉钉..."

python3 "$SCRIPTS_DIR/send_to_dingtalk.py" \
    --date "$TARGET_DATE" \
    --report "$REPORT_FILE" 2>&1 | tee -a "$LOG_DIR/auto_push.log"

if [ $? -eq 0 ]; then
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "  ✅ 流程完成 - $TARGET_DATE"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    log "❌ 推送失败"
    exit 1
fi
