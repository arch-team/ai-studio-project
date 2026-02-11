#!/usr/bin/env bash
# =============================================================================
# CDK Diff 安全门控脚本
# =============================================================================
# 功能: 执行 cdk diff 并解析输出，检测破坏性变更的危险信号
#
# 检测规则:
#   ERROR (退出码 1):
#     - 资源替换: "requires replacement" 或 "may cause replacement"
#     - 有状态资源删除: [-] AWS::RDS::DBCluster, DBInstance, FSx, S3::Bucket
#   WARNING (退出码 0，打印警告):
#     - Export Name 变更: Output 中 export_name 修改
#
# 用法:
#   ./scripts/diff-safety-check.sh [--env dev|staging|prod]
#
# 兼容性: macOS (bash 3.2+) 和 Linux
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 颜色定义（兼容 macOS 和 Linux）
# ---------------------------------------------------------------------------
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# 默认参数
# ---------------------------------------------------------------------------
ENV="dev"
REGION="${AWS_REGION:-us-east-1}"

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --env)
            if [ -n "${2:-}" ]; then
                ENV="$2"
                shift 2
            else
                echo -e "${RED}错误: --env 需要参数值${RESET}" >&2
                exit 2
            fi
            ;;
        --env=*)
            ENV="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [--env dev|staging|prod]"
            echo ""
            echo "选项:"
            echo "  --env ENV    指定环境 (默认: dev)"
            echo "  --help       显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 '$1'${RESET}" >&2
            exit 2
            ;;
    esac
done

# 验证环境参数
case "$ENV" in
    dev|staging|prod) ;;
    *)
        echo -e "${RED}错误: 无效的环境 '$ENV'，支持: dev, staging, prod${RESET}" >&2
        exit 2
        ;;
esac

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
echo -e "${CYAN}${BOLD}=== CDK Diff 安全门控检查 ===${RESET}"
echo -e "${CYAN}环境: ${ENV}  区域: ${REGION}${RESET}"
echo ""

# 执行 cdk diff，捕获全部输出（包括 stderr）
# cdk diff 在有差异时返回非零退出码，所以不能直接用 set -e
echo -e "${CYAN}正在执行 cdk diff ...${RESET}"
DIFF_OUTPUT=""
DIFF_EXIT_CODE=0
DIFF_OUTPUT=$(AWS_REGION="${REGION}" cdk diff --context "env=${ENV}" 2>&1) || DIFF_EXIT_CODE=$?

# cdk diff 退出码: 0=无差异, 1=有差异, 2=错误
if [ "$DIFF_EXIT_CODE" -eq 2 ]; then
    echo -e "${RED}错误: cdk diff 执行失败 (exit code: ${DIFF_EXIT_CODE})${RESET}"
    echo "$DIFF_OUTPUT"
    exit 2
fi

if [ "$DIFF_EXIT_CODE" -eq 0 ] && [ -z "$DIFF_OUTPUT" ]; then
    echo -e "${GREEN}无变更，所有 Stack 与已部署状态一致。${RESET}"
    exit 0
fi

# ---------------------------------------------------------------------------
# 解析 diff 输出：统计变更摘要
# ---------------------------------------------------------------------------

# 统计涉及的 Stack 数量（匹配 "Stack <StackName>" 行）
STACK_COUNT=0
STACK_COUNT=$(echo "$DIFF_OUTPUT" | grep -c "^Stack " 2>/dev/null || true)

# 统计新增资源 [+]
ADD_COUNT=0
ADD_COUNT=$(echo "$DIFF_OUTPUT" | grep -c '^\[+\]' 2>/dev/null || true)

# 统计修改资源 [~]
MODIFY_COUNT=0
MODIFY_COUNT=$(echo "$DIFF_OUTPUT" | grep -c '^\[~\]' 2>/dev/null || true)

# 统计删除资源 [-]
DELETE_COUNT=0
DELETE_COUNT=$(echo "$DIFF_OUTPUT" | grep -c '^\[-\]' 2>/dev/null || true)

echo -e "${BOLD}--- Diff 摘要 ---${RESET}"
echo -e "  变更 Stack 数:  ${STACK_COUNT}"
echo -e "  新增资源 [+]:   ${GREEN}${ADD_COUNT}${RESET}"
echo -e "  修改资源 [~]:   ${YELLOW}${MODIFY_COUNT}${RESET}"
echo -e "  删除资源 [-]:   ${RED}${DELETE_COUNT}${RESET}"
echo ""

# ---------------------------------------------------------------------------
# 危险信号检测
# ---------------------------------------------------------------------------
ERROR_COUNT=0
WARNING_COUNT=0
ERROR_DETAILS=""
WARNING_DETAILS=""

# --- 检测 1: 资源替换 (requires replacement / may cause replacement) ---
REPLACEMENT_LINES=""
REPLACEMENT_LINES=$(echo "$DIFF_OUTPUT" | grep -in "requires replacement\|may cause replacement" 2>/dev/null || true)
if [ -n "$REPLACEMENT_LINES" ]; then
    MATCH_COUNT=$(echo "$REPLACEMENT_LINES" | wc -l | tr -d ' ')
    ERROR_COUNT=$((ERROR_COUNT + MATCH_COUNT))
    ERROR_DETAILS="${ERROR_DETAILS}
  [REPLACEMENT] 检测到 ${MATCH_COUNT} 处资源替换:
$(echo "$REPLACEMENT_LINES" | while IFS= read -r line; do echo "    - ${line}"; done)"
fi

# --- 检测 2: 有状态资源删除 ---
# 检测 [-] 后跟关键有状态资源类型
STATEFUL_TYPES="AWS::RDS::DBCluster\|AWS::RDS::DBInstance\|AWS::FSx::FileSystem\|AWS::S3::Bucket"
STATEFUL_DELETE_LINES=""
STATEFUL_DELETE_LINES=$(echo "$DIFF_OUTPUT" | grep "^\[-\]" | grep "${STATEFUL_TYPES}" 2>/dev/null || true)
if [ -n "$STATEFUL_DELETE_LINES" ]; then
    MATCH_COUNT=$(echo "$STATEFUL_DELETE_LINES" | wc -l | tr -d ' ')
    ERROR_COUNT=$((ERROR_COUNT + MATCH_COUNT))
    ERROR_DETAILS="${ERROR_DETAILS}
  [STATEFUL DELETE] 检测到 ${MATCH_COUNT} 处有状态资源删除:
$(echo "$STATEFUL_DELETE_LINES" | while IFS= read -r line; do echo "    - ${line}"; done)"
fi

# --- 检测 3: Export Name 变更 ---
# 检测 Output section 中 export_name 变更模式
EXPORT_CHANGE_LINES=""
EXPORT_CHANGE_LINES=$(echo "$DIFF_OUTPUT" | grep '\[~\].*Output.*Export\|export.*Name' 2>/dev/null || true)
if [ -n "$EXPORT_CHANGE_LINES" ]; then
    MATCH_COUNT=$(echo "$EXPORT_CHANGE_LINES" | wc -l | tr -d ' ')
    WARNING_COUNT=$((WARNING_COUNT + MATCH_COUNT))
    WARNING_DETAILS="${WARNING_DETAILS}
  [EXPORT NAME] 检测到 ${MATCH_COUNT} 处 Export Name 变更:
$(echo "$EXPORT_CHANGE_LINES" | while IFS= read -r line; do echo "    - ${line}"; done)"
fi

# ---------------------------------------------------------------------------
# 输出检测结果
# ---------------------------------------------------------------------------
echo -e "${BOLD}--- 安全检查结果 ---${RESET}"

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${RED}${BOLD}ERROR: 检测到 ${ERROR_COUNT} 个高风险变更!${RESET}"
    echo -e "${RED}${ERROR_DETAILS}${RESET}"
    echo ""
fi

if [ "$WARNING_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}${BOLD}WARNING: 检测到 ${WARNING_COUNT} 个需关注的变更${RESET}"
    echo -e "${YELLOW}${WARNING_DETAILS}${RESET}"
    echo ""
fi

if [ "$ERROR_COUNT" -eq 0 ] && [ "$WARNING_COUNT" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}PASS: 未检测到危险信号${RESET}"
    echo ""
fi

# ---------------------------------------------------------------------------
# 退出码决策
# ---------------------------------------------------------------------------
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${RED}${BOLD}>>> 安全检查未通过! 请检查上述 ERROR 项后再继续部署。${RESET}"
    echo -e "${RED}提示: 如确认变更安全，可在 CR 中说明原因后手动部署。${RESET}"
    exit 1
else
    if [ "$WARNING_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}>>> 安全检查通过 (有警告)。请在部署前确认上述 WARNING 项。${RESET}"
    else
        echo -e "${GREEN}>>> 安全检查通过。可以继续部署。${RESET}"
    fi
    exit 0
fi
