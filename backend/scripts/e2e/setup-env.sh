#!/bin/bash
# =============================================================================
# E2E 测试环境初始化脚本
# =============================================================================
# 功能：
#   1. 验证 AWS 凭证
#   2. 配置 EKS kubectl 上下文
#   3. 验证/检查 Task Governance 配置
#   4. 验证 Kueue ClusterQueue 配置
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# -----------------------------------------------------------------------------
# 1. 加载配置
# -----------------------------------------------------------------------------
log_section "加载配置"

# 支持通过环境变量指定配置文件
ENV_FILE="${E2E_ENV:-.env.e2e.dev}"

if [[ -f "$BACKEND_DIR/$ENV_FILE" ]]; then
    log_info "加载配置文件: $BACKEND_DIR/$ENV_FILE"
    set -a
    source "$BACKEND_DIR/$ENV_FILE"
    set +a
elif [[ -f "$BACKEND_DIR/.env.e2e" ]]; then
    log_info "加载配置文件: $BACKEND_DIR/.env.e2e"
    set -a
    source "$BACKEND_DIR/.env.e2e"
    set +a
else
    log_error "配置文件不存在: $BACKEND_DIR/$ENV_FILE"
    log_info "请先创建配置文件:"
    log_info "  cp $BACKEND_DIR/.env.e2e.example $BACKEND_DIR/.env.e2e.dev"
    exit 1
fi

# 检查必填配置
if [[ -z "${HYPERPOD_CLUSTER_NAME:-}" ]]; then
    log_error "HYPERPOD_CLUSTER_NAME 未配置"
    exit 1
fi

if [[ -z "${AWS_REGION:-}" ]]; then
    AWS_REGION="us-east-1"
    log_warn "AWS_REGION 未配置，使用默认值: $AWS_REGION"
fi

# -----------------------------------------------------------------------------
# 2. 验证 AWS 凭证
# -----------------------------------------------------------------------------
log_section "验证 AWS 凭证"

if ! command -v aws &>/dev/null; then
    log_error "AWS CLI 未安装，请先安装: https://aws.amazon.com/cli/"
    exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
    log_error "AWS 凭证无效，请先登录："
    log_info "  aws sso login --profile your-profile"
    log_info "  或设置环境变量 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY"
    exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity --output json)
CURRENT_ACCOUNT=$(echo "$CALLER_IDENTITY" | jq -r '.Account')
CURRENT_ARN=$(echo "$CALLER_IDENTITY" | jq -r '.Arn')
log_info "当前身份: $CURRENT_ARN"
log_info "AWS 账号: $CURRENT_ACCOUNT"

# 验证账号 ID 是否匹配
if [[ -n "${AWS_ACCOUNT_ID:-}" && "$AWS_ACCOUNT_ID" != "$CURRENT_ACCOUNT" ]]; then
    log_warn "配置的 AWS_ACCOUNT_ID ($AWS_ACCOUNT_ID) 与当前账号 ($CURRENT_ACCOUNT) 不匹配"
fi

# -----------------------------------------------------------------------------
# 3. 配置 EKS kubectl 上下文
# -----------------------------------------------------------------------------
log_section "配置 EKS kubectl 上下文"

if ! command -v kubectl &>/dev/null; then
    log_error "kubectl 未安装，请先安装"
    exit 1
fi

if [[ -n "${HYPERPOD_EKS_CLUSTER_NAME:-}" ]]; then
    log_info "更新 kubeconfig: $HYPERPOD_EKS_CLUSTER_NAME"
    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$HYPERPOD_EKS_CLUSTER_NAME" \
        2>/dev/null || log_warn "EKS kubeconfig 更新失败，可能已是 HyperPod 上下文"
fi

# 检查 kubectl 连接
if kubectl cluster-info &>/dev/null; then
    CURRENT_CONTEXT=$(kubectl config current-context)
    log_info "kubectl 上下文: $CURRENT_CONTEXT"
else
    log_warn "kubectl 无法连接到集群"
fi

# -----------------------------------------------------------------------------
# 4. 验证 Task Governance 配置
# -----------------------------------------------------------------------------
log_section "验证 Task Governance 配置"

# 获取集群 ARN
CLUSTER_ARN="arn:aws:sagemaker:${AWS_REGION}:${CURRENT_ACCOUNT}:cluster/${HYPERPOD_CLUSTER_NAME}"
log_info "集群 ARN: $CLUSTER_ARN"

# 检查 Cluster Scheduler Config
log_info "检查 Cluster Scheduler Config..."
SCHEDULER_CONFIGS=$(aws sagemaker list-cluster-scheduler-configs \
    --cluster-arn "$CLUSTER_ARN" \
    --output json 2>/dev/null || echo "{}")

if [[ $(echo "$SCHEDULER_CONFIGS" | jq -r '.ClusterSchedulerConfigSummaries // [] | length') -gt 0 ]]; then
    log_info "✅ Cluster Scheduler Config 已配置"
    echo "$SCHEDULER_CONFIGS" | jq -r '.ClusterSchedulerConfigSummaries[] | "  - \(.Name)"'
else
    log_warn "⚠️ Cluster Scheduler Config 未配置"
    log_info "请参考文档配置 Task Governance"
fi

# 检查 Compute Quotas
log_info "检查 Compute Quotas..."
QUOTAS=$(aws sagemaker list-compute-quotas \
    --cluster-arn "$CLUSTER_ARN" \
    --output json 2>/dev/null || echo "{}")

if [[ $(echo "$QUOTAS" | jq -r '.ComputeQuotaSummaries // [] | length') -gt 0 ]]; then
    log_info "✅ Compute Quotas 已配置"
    echo "$QUOTAS" | jq -r '.ComputeQuotaSummaries[] | "  - \(.Name): \(.Status)"'
else
    log_warn "⚠️ Compute Quotas 未配置"
fi

# -----------------------------------------------------------------------------
# 5. 验证 Kueue ClusterQueue 配置
# -----------------------------------------------------------------------------
log_section "验证 Kueue ClusterQueue 配置"

if kubectl get clusterqueues &>/dev/null; then
    log_info "ClusterQueue 列表:"
    kubectl get clusterqueues -o custom-columns=NAME:.metadata.name,COHORT:.spec.cohort 2>/dev/null || true

    # 检查 E2E 测试用的队列
    LOW_QUEUE="${E2E_LOW_QUEUE_NAME:-hyperpod-ns-e2e-low-localqueue}"
    HIGH_QUEUE="${E2E_HIGH_QUEUE_NAME:-hyperpod-ns-e2e-high-localqueue}"

    # 提取 ClusterQueue 名称（去掉 -localqueue 后缀）
    LOW_CQ="${LOW_QUEUE%-localqueue}"
    HIGH_CQ="${HIGH_QUEUE%-localqueue}"

    if kubectl get clusterqueue "$LOW_CQ" &>/dev/null; then
        log_info "✅ 低优先级 ClusterQueue 存在: $LOW_CQ"
    else
        log_warn "⚠️ 低优先级 ClusterQueue 不存在: $LOW_CQ"
    fi

    if kubectl get clusterqueue "$HIGH_CQ" &>/dev/null; then
        log_info "✅ 高优先级 ClusterQueue 存在: $HIGH_CQ"
    else
        log_warn "⚠️ 高优先级 ClusterQueue 不存在: $HIGH_CQ"
    fi
else
    log_warn "无法获取 ClusterQueue（可能 Kueue 未安装或权限不足）"
fi

# -----------------------------------------------------------------------------
# 6. 验证 PriorityClass 配置
# -----------------------------------------------------------------------------
log_section "验证 PriorityClass 配置"

if kubectl get priorityclasses &>/dev/null; then
    log_info "检查 WorkloadPriorityClass..."
    if kubectl get priorityclasses | grep -E "low-priority|high-priority" &>/dev/null; then
        log_info "✅ PriorityClass 已配置"
        kubectl get priorityclasses | grep -E "low-priority|high-priority" | while read -r line; do
            echo "  $line"
        done
    else
        log_warn "⚠️ E2E 测试用 PriorityClass 未找到"
    fi
else
    log_warn "无法获取 PriorityClass"
fi

# -----------------------------------------------------------------------------
# 7. 输出摘要
# -----------------------------------------------------------------------------
log_section "环境配置摘要"

echo "AWS Region:        ${AWS_REGION}"
echo "AWS Account:       ${CURRENT_ACCOUNT}"
echo "HyperPod Cluster:  ${HYPERPOD_CLUSTER_NAME}"
echo "EKS Cluster:       ${HYPERPOD_EKS_CLUSTER_NAME:-N/A}"
echo "Low Priority NS:   ${E2E_LOW_NAMESPACE:-hyperpod-ns-e2e-low}"
echo "High Priority NS:  ${E2E_HIGH_NAMESPACE:-hyperpod-ns-e2e-high}"
echo "Read-Only Mode:    ${E2E_READ_ONLY:-true}"

echo ""
log_info "环境初始化完成！"
log_info "运行测试: pytest tests/e2e/aws/ -v -m 'not slow'"
