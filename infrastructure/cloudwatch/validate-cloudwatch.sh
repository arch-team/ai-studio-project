#!/usr/bin/env bash
# CloudWatch Logs 配置验证脚本
# 验证日志组存在性、留存策略、KMS 加密配置
#
# 使用方式:
#   chmod +x validate-cloudwatch.sh
#   ./validate-cloudwatch.sh --region us-east-1 --env dev
#
# 依赖: AWS CLI v2, jq

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 默认参数
REGION="us-east-1"
ENVIRONMENT="dev"
LOG_GROUP_PREFIX="/aws/hyperpod/training-platform"
REPORT_FILE=""
EXIT_CODE=0

# 使用说明
usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --region REGION       AWS 区域 (默认: us-east-1)"
    echo "  --env ENV             环境名称: dev|staging|prod (默认: dev)"
    echo "  --report FILE         输出验证报告到文件"
    echo "  -h, --help            显示帮助信息"
    exit 0
}

# 参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --region) REGION="$2"; shift 2 ;;
        --env) ENVIRONMENT="$2"; shift 2 ;;
        --report) REPORT_FILE="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
done

# 日志输出函数
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; EXIT_CODE=1; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_info() { echo -e "      $1"; }

# 报告输出
report_line() {
    if [[ -n "$REPORT_FILE" ]]; then
        echo "$1" >> "$REPORT_FILE"
    fi
}

echo "============================================"
echo "CloudWatch Logs 配置验证"
echo "============================================"
echo "区域: $REGION"
echo "环境: $ENVIRONMENT"
echo "日志组前缀: $LOG_GROUP_PREFIX"
echo "时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"
echo ""

if [[ -n "$REPORT_FILE" ]]; then
    echo "# CloudWatch Logs 验证报告" > "$REPORT_FILE"
    echo "日期: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$REPORT_FILE"
    echo "环境: $ENVIRONMENT | 区域: $REGION" >> "$REPORT_FILE"
    echo "---" >> "$REPORT_FILE"
fi

# 预期日志组及其留存策略 (天数)
declare -A EXPECTED_LOG_GROUPS
EXPECTED_LOG_GROUPS["${LOG_GROUP_PREFIX}"]=30
EXPECTED_LOG_GROUPS["${LOG_GROUP_PREFIX}/api"]=30
EXPECTED_LOG_GROUPS["${LOG_GROUP_PREFIX}/training-jobs"]=90
EXPECTED_LOG_GROUPS["${LOG_GROUP_PREFIX}/audit"]=365

# ============================================================
# 1. 验证日志组存在性
# ============================================================
echo "--- 1. 日志组存在性验证 ---"
report_line ""
report_line "## 1. 日志组存在性"

for log_group in "${!EXPECTED_LOG_GROUPS[@]}"; do
    result=$(aws logs describe-log-groups \
        --log-group-name-prefix "$log_group" \
        --region "$REGION" \
        --query "logGroups[?logGroupName=='${log_group}'].logGroupName" \
        --output text 2>/dev/null || echo "")

    if [[ "$result" == "$log_group" ]]; then
        log_pass "日志组存在: $log_group"
        report_line "- [PASS] $log_group"
    else
        log_fail "日志组不存在: $log_group"
        report_line "- [FAIL] $log_group - 不存在"
    fi
done
echo ""

# ============================================================
# 2. 验证留存策略
# ============================================================
echo "--- 2. 留存策略验证 ---"
report_line ""
report_line "## 2. 留存策略"

for log_group in "${!EXPECTED_LOG_GROUPS[@]}"; do
    expected_retention=${EXPECTED_LOG_GROUPS[$log_group]}

    actual_retention=$(aws logs describe-log-groups \
        --log-group-name-prefix "$log_group" \
        --region "$REGION" \
        --query "logGroups[?logGroupName=='${log_group}'].retentionInDays | [0]" \
        --output text 2>/dev/null || echo "None")

    if [[ "$actual_retention" == "None" ]] || [[ "$actual_retention" == "null" ]]; then
        log_warn "日志组 $log_group 未设置留存策略 (永不过期)"
        report_line "- [WARN] $log_group: 未设置留存策略"
    elif [[ "$actual_retention" == "$expected_retention" ]]; then
        log_pass "日志组 $log_group 留存策略正确: ${actual_retention} 天"
        report_line "- [PASS] $log_group: ${actual_retention} 天"
    else
        log_fail "日志组 $log_group 留存策略不匹配: 期望 ${expected_retention} 天, 实际 ${actual_retention} 天"
        report_line "- [FAIL] $log_group: 期望 ${expected_retention} 天, 实际 ${actual_retention} 天"
    fi
done
echo ""

# ============================================================
# 3. 验证 KMS 加密
# ============================================================
echo "--- 3. KMS 加密验证 ---"
report_line ""
report_line "## 3. KMS 加密"

for log_group in "${!EXPECTED_LOG_GROUPS[@]}"; do
    kms_key=$(aws logs describe-log-groups \
        --log-group-name-prefix "$log_group" \
        --region "$REGION" \
        --query "logGroups[?logGroupName=='${log_group}'].kmsKeyId | [0]" \
        --output text 2>/dev/null || echo "None")

    if [[ "$kms_key" == "None" ]] || [[ "$kms_key" == "null" ]] || [[ -z "$kms_key" ]]; then
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            log_fail "日志组 $log_group 未启用 KMS 加密 (生产环境必须启用)"
            report_line "- [FAIL] $log_group: 未启用 KMS 加密"
        else
            log_warn "日志组 $log_group 未启用 KMS 加密 (非生产环境可选)"
            report_line "- [WARN] $log_group: 未启用 KMS 加密"
        fi
    else
        log_pass "日志组 $log_group 已启用 KMS 加密: ${kms_key}"
        report_line "- [PASS] $log_group: KMS Key ${kms_key}"
    fi
done
echo ""

# ============================================================
# 4. 验证 Metric Filters (可选)
# ============================================================
echo "--- 4. 指标过滤器验证 ---"
report_line ""
report_line "## 4. 指标过滤器"

# 检查是否存在关键指标过滤器
EXPECTED_METRICS=("ErrorCount" "5xxCount" "SlowRequests")
for metric_name in "${EXPECTED_METRICS[@]}"; do
    found=false
    for log_group in "${!EXPECTED_LOG_GROUPS[@]}"; do
        result=$(aws logs describe-metric-filters \
            --log-group-name "$log_group" \
            --region "$REGION" \
            --query "metricFilters[?filterName=='${metric_name}'].filterName" \
            --output text 2>/dev/null || echo "")
        if [[ -n "$result" ]]; then
            found=true
            log_pass "指标过滤器 $metric_name 存在于 $log_group"
            report_line "- [PASS] $metric_name 在 $log_group"
            break
        fi
    done
    if [[ "$found" == "false" ]]; then
        log_warn "指标过滤器 $metric_name 未找到 (建议配置)"
        report_line "- [WARN] $metric_name 未配置"
    fi
done
echo ""

# ============================================================
# 5. 汇总
# ============================================================
echo "============================================"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}验证通过${NC}: 所有检查项均通过"
else
    echo -e "${RED}验证失败${NC}: 存在不符合配置要求的项"
fi
echo "============================================"

report_line ""
report_line "## 总结"
if [[ $EXIT_CODE -eq 0 ]]; then
    report_line "验证结果: **通过**"
else
    report_line "验证结果: **失败**"
fi

exit $EXIT_CODE
