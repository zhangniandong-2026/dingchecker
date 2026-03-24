#!/bin/bash
# 业务单元配置管理工具

CONFIG_FILE=~/dingtalk_checker/config/business_units.txt
CONFIG_DIR=~/dingtalk_checker/config

# 确保目录存在
mkdir -p "$CONFIG_DIR"

# 如果配置文件不存在，创建默认配置
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
# 业务单元配置文件
# 每行一个单元名称，支持注释（#开头）和空行

# 核心业务单元
媒体军工组
交通行业组
政府行业一组
政府行业二组
能源组
央企组

# 新增业务单元（示例，可修改）
# 金融组
# 医疗组
# 教育组
EOF
    echo "✓ 已创建默认配置文件: $CONFIG_FILE"
fi

# 显示帮助
show_help() {
    cat << EOF
业务单元配置管理工具

用法:
  $0 [命令]

命令:
  list        列出当前配置的所有业务单元
  add         添加新的业务单元
  edit        编辑配置文件
  show        显示配置文件内容
  backup      备份配置文件
  restore     恢复备份
  reset       重置为默认配置
  help        显示此帮助信息

示例:
  $0 list                    # 列出所有单元
  $0 add "新业务单元"         # 添加新单元
  $0 edit                    # 编辑配置
  $0 backup                  # 备份配置

配置文件位置: $CONFIG_FILE
EOF
}

# 列出所有业务单元
list_units() {
    echo "========================================"
    echo "当前配置的业务单元"
    echo "========================================"
    echo ""

    count=0
    while IFS= read -r line; do
        # 跳过空行和注释
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            count=$((count + 1))
            echo "  $count. $line"
        fi
    done < "$CONFIG_FILE"

    echo ""
    echo "总计: $count 个业务单元"
    echo ""
}

# 添加业务单元
add_unit() {
    if [ -z "$1" ]; then
        echo "请输入业务单元名称:"
        read -r unit_name
    else
        unit_name="$1"
    fi

    if [ -z "$unit_name" ]; then
        echo "❌ 单元名称不能为空"
        exit 1
    fi

    # 检查是否已存在
    if grep -qF "$unit_name" "$CONFIG_FILE"; then
        echo "⚠️  单元 '$unit_name' 已存在"
        exit 0
    fi

    # 添加到文件末尾
    echo "$unit_name" >> "$CONFIG_FILE"
    echo "✓ 已添加: $unit_name"
    echo ""
    list_units
}

# 编辑配置文件
edit_config() {
    # 检测编辑器
    if [ -n "$EDITOR" ]; then
        $EDITOR "$CONFIG_FILE"
    elif command -v nano &> /dev/null; then
        nano "$CONFIG_FILE"
    elif command -v vim &> /dev/null; then
        vim "$CONFIG_FILE"
    elif command -v vi &> /dev/null; then
        vi "$CONFIG_FILE"
    else
        echo "❌ 未找到文本编辑器"
        echo "可以手动编辑: $CONFIG_FILE"
        exit 1
    fi

    echo ""
    echo "✓ 配置已更新"
    echo ""
    list_units
}

# 显示配置文件
show_config() {
    echo "========================================"
    echo "配置文件内容"
    echo "========================================"
    echo ""
    cat -n "$CONFIG_FILE"
    echo ""
}

# 备份配置
backup_config() {
    backup_file="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CONFIG_FILE" "$backup_file"
    echo "✓ 配置已备份到: $backup_file"
}

# 恢复备份
restore_config() {
    # 查找最新的备份
    latest_backup=$(ls -t "${CONFIG_FILE}.backup."* 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        echo "❌ 未找到备份文件"
        exit 1
    fi

    echo "找到备份: $latest_backup"
    echo "确认恢复? (y/n)"
    read -r confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        cp "$latest_backup" "$CONFIG_FILE"
        echo "✓ 配置已恢复"
        echo ""
        list_units
    else
        echo "已取消"
    fi
}

# 重置为默认配置
reset_config() {
    echo "⚠️  警告: 这将重置为默认的 6 个业务单元"
    echo "确认重置? (y/n)"
    read -r confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        # 先备份
        backup_config

        # 重置
        cat > "$CONFIG_FILE" << 'EOF'
# 业务单元配置文件
# 每行一个单元名称，支持注释（#开头）和空行

媒体军工组
交通行业组
政府行业一组
政府行业二组
能源组
央企组
EOF
        echo "✓ 配置已重置为默认"
        echo ""
        list_units
    else
        echo "已取消"
    fi
}

# 主程序
case "${1:-help}" in
    list|ls)
        list_units
        ;;
    add)
        add_unit "$2"
        ;;
    edit|e)
        edit_config
        ;;
    show|cat)
        show_config
        ;;
    backup|bak)
        backup_config
        ;;
    restore)
        restore_config
        ;;
    reset)
        reset_config
        ;;
    help|h|-h|--help)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
