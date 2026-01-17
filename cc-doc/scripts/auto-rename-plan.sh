#!/bin/bash
# Auto-rename Claude Code plan files
# Usage: ./auto-rename-plan.sh [command] [-d|--dir <path>]

set -euo pipefail

# 默认配置
DEFAULT_PLANS_DIR="$(cd "$(dirname "$0")/../plans" 2>/dev/null && pwd || echo "")"
PLANS_DIR=""
INDEX_FILE=""
readonly DATE_FORMAT="%Y-%m-%d"
readonly MAX_SLUG_LENGTH=50

# 设置目录
set_plans_dir() {
    PLANS_DIR="${1:-$DEFAULT_PLANS_DIR}"
    if [[ -z "$PLANS_DIR" || ! -d "$PLANS_DIR" ]]; then
        echo "❌ 目录不存在: $PLANS_DIR"
        exit 1
    fi
    PLANS_DIR="$(cd "$PLANS_DIR" && pwd)"
    INDEX_FILE="$PLANS_DIR/INDEX.md"
}

# 从标题生成 slug
generate_slug() {
    echo "$1" | perl -CSD -pe '
        s/^#\s+(Plan:\s+)?//;                  # 移除 # 和 Plan: 前缀
        $_ = lc($_);                            # 转小写
        s/[^\p{Han}a-z0-9]+/-/g;               # 非中文/英文/数字替换为连字符
        s/-+/-/g;                               # 合并连续连字符
        s/^-|-$//g;                             # 去除首尾连字符
        $_ = substr($_, 0, '"$MAX_SLUG_LENGTH"');  # 截断长度
    '
}

# 检查是否为随机命名（形如 word-word-word[-suffix].md）
is_random_name() {
    # 匹配 3+ 个小写单词用连字符连接，可带后缀
    [[ "$1" =~ ^[a-z]+-[a-z]+-[a-z]+(-[a-z0-9]+)*\.md$ ]]
}

# 生成唯一文件名
generate_unique_filename() {
    local base_name="$1"
    local filepath="$PLANS_DIR/$base_name"
    local counter=0

    while [[ -f "$filepath" ]]; do
        ((counter++))
        filepath="$PLANS_DIR/${base_name%.md}-${counter}.md"
    done

    basename "$filepath"
}

# 清理标题文本
clean_title() {
    echo "$1" | perl -pe 's/^#\s+(Plan:\s+)?//'
}

# 初始化索引文件
init_index() {
    [[ -f "$INDEX_FILE" ]] && return 0

    cat > "$INDEX_FILE" << 'EOF'
# Plans 索引

Claude Code 生成的计划文件索引。

## 命名规范

重命名文件时请使用格式：`YYYY-MM-DD-<简短描述>.md`

## 索引

| 日期 | 文件名 | 描述 | 状态 |
|------|--------|------|------|
EOF
}

# 重命名单个文件
rename_plan() {
    local filepath="$1"
    local filename=$(basename "$filepath")

    # 跳过非目标文件
    [[ "$filename" == "INDEX.md" ]] && return 0
    is_random_name "$filename" || return 0

    # 读取标题
    local title=$(head -1 "$filepath" 2>/dev/null)
    if [[ -z "$title" || ! "$title" =~ ^# ]]; then
        echo "⚠️  跳过: $filename (无有效标题)"
        return 1
    fi

    # 生成新文件名
    local date=$(date +"$DATE_FORMAT")
    local slug=$(generate_slug "$title")
    local new_filename=$(generate_unique_filename "${date}-${slug}.md")

    # 执行重命名
    mv "$filepath" "$PLANS_DIR/$new_filename"
    echo "✅ 重命名: $filename → $new_filename"

    # 更新索引
    init_index
    local clean_title=$(clean_title "$title")
    echo "| $date | \`$new_filename\` | $clean_title | ⏳ 进行中 |" >> "$INDEX_FILE"
    echo "📝 已更新 INDEX.md"
}

# 处理所有现有文件
process_existing() {
    local count=0
    for file in "$PLANS_DIR"/*.md; do
        [[ -f "$file" ]] || continue
        rename_plan "$file" && ((count++)) || true
    done

    [[ $count -eq 0 ]] && echo "ℹ️  没有需要重命名的文件" || true
}

# 监控模式
watch_mode() {
    # 检查 fswatch
    if ! command -v fswatch &> /dev/null; then
        echo "❌ 需要安装 fswatch:"
        echo "  macOS: brew install fswatch"
        echo "  Linux: apt-get install fswatch 或 yum install fswatch"
        exit 1
    fi

    echo "👀 监控 $PLANS_DIR 中的新文件..."
    echo "按 Ctrl+C 停止"

    # 先处理现有文件
    process_existing

    # 监控新文件
    fswatch -0 --event=Created "$PLANS_DIR" | while IFS= read -r -d '' event; do
        [[ "$event" == *.md ]] || continue
        sleep 1  # 等待文件写入完成
        rename_plan "$event"
    done
}

# 显示帮助
show_help() {
    cat << EOF
用法: $(basename "$0") [命令] [选项]

命令:
  once   处理现有文件后退出（默认）
  watch  持续监控目录，自动重命名新文件
  help   显示此帮助信息

选项:
  -d, --dir <path>  指定 plans 目录路径

示例:
  $(basename "$0")                           # 处理默认目录
  $(basename "$0") once -d ~/.claude/plans   # 处理指定目录
  $(basename "$0") watch                     # 持续监控默认目录
EOF
}

# 主入口
main() {
    local cmd="once"
    local custom_dir=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--dir)
                custom_dir="$2"
                shift 2
                ;;
            watch|once)
                cmd="$1"
                shift
                ;;
            help|--help|-h)
                show_help
                exit 0
                ;;
            *)
                echo "❌ 未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 设置目录
    set_plans_dir "$custom_dir"
    echo "📂 处理目录: $PLANS_DIR"

    # 执行命令
    case "$cmd" in
        watch)  watch_mode ;;
        once)   process_existing ;;
    esac
}

main "$@"