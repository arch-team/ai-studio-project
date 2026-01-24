#!/bin/bash
# =============================================================================
# E2E 测试环境初始化脚本
# =============================================================================

set -euo pipefail

# 导入共享函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# -----------------------------------------------------------------------------
# 1. 加载配置
# -----------------------------------------------------------------------------
log_section "加载配置"

if ! load_env_config; then
    exit 1
fi

# 检查必填配置
if [[ -z "${HYPERPOD_CLUSTER_NAME:-}" ]]; then
    log_error "HYPERPOD_CLUSTER_NAME 未配置"
    exit 1
fi

AWS_REGION="${AWS_REGION:-us-east-1}"

# -----------------------------------------------------------------------------
# 2. 验证 AWS 凭证
# -----------------------------------------------------------------------------
log_section "验证 AWS 凭证"

if ! check_aws_credentials; then
    exit 1
fi

CURRENT_ACCOUNT=$(get_aws_account_info)
log_info "AWS 账号: $CURRENT_ACCOUNT"

# 验证账号匹配
if [[ -n "${AWS_ACCOUNT_ID:-}" && "$AWS_ACCOUNT_ID" != "$CURRENT_ACCOUNT" ]]; then
    log_warn "配置账号与当前账号不匹配"
fi

# -----------------------------------------------------------------------------
# 3. 配置 EKS kubectl
# -----------------------------------------------------------------------------
log_section "配置 EKS kubectl"

if ! check_kubectl; then
    exit 1
fi

if [[ -n "${HYPERPOD_EKS_CLUSTER_NAME:-}" ]]; then
    log_info "更新 kubeconfig: $HYPERPOD_EKS_CLUSTER_NAME"
    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$HYPERPOD_EKS_CLUSTER_NAME" \
        2>/dev/null || log_warn "更新失败（可能已配置）"
fi

# -----------------------------------------------------------------------------
# 4. 验证 Task Governance
# -----------------------------------------------------------------------------
log_section "验证 Task Governance"

CLUSTER_ARN=$(get_cluster_arn "$HYPERPOD_CLUSTER_NAME")
log_info "集群 ARN: $CLUSTER_ARN"

# 检查 Scheduler Config
CONFIGS=$(aws sagemaker list-cluster-scheduler-configs \
    --cluster-arn "$CLUSTER_ARN" \
    --output json 2>/dev/null || echo "{}")

if [[ $(echo "$CONFIGS" | jq '.ClusterSchedulerConfigSummaries // [] | length') -gt 0 ]]; then
    log_info "✅ Scheduler Config 已配置"
else
    log_warn "⚠️ Scheduler Config 未配置"
fi

# 检查 Compute Quotas
QUOTAS=$(aws sagemaker list-compute-quotas \
    --cluster-arn "$CLUSTER_ARN" \
    --output json 2>/dev/null || echo "{}")

if [[ $(echo "$QUOTAS" | jq '.ComputeQuotaSummaries // [] | length') -gt 0 ]]; then
    log_info "✅ Compute Quotas 已配置"
else
    log_warn "⚠️ Compute Quotas 未配置"
fi

# -----------------------------------------------------------------------------
# 5. 验证 Kueue 配置
# -----------------------------------------------------------------------------
log_section "验证 Kueue 配置"

if kubectl get clusterqueues &>/dev/null; then
    # 检查测试队列
    for queue_var in E2E_LOW_QUEUE_NAME E2E_HIGH_QUEUE_NAME; do
        queue_name="${!queue_var:-}"
        if [[ -n "$queue_name" ]]; then
            cq_name="${queue_name%-localqueue}"
            if kubectl get clusterqueue "$cq_name" &>/dev/null; then
                log_info "✅ ClusterQueue: $cq_name"
            else
                log_warn "⚠️ ClusterQueue 不存在: $cq_name"
            fi
        fi
    done
else
    log_warn "无法获取 ClusterQueue"
fi

# -----------------------------------------------------------------------------
# 6. 输出摘要
# -----------------------------------------------------------------------------
log_section "环境摘要"

cat <<EOF
AWS Region:       ${AWS_REGION}
AWS Account:      ${CURRENT_ACCOUNT}
HyperPod Cluster: ${HYPERPOD_CLUSTER_NAME}
EKS Cluster:      ${HYPERPOD_EKS_CLUSTER_NAME:-N/A}
Read-Only Mode:   ${E2E_READ_ONLY:-true}
EOF

echo ""
log_info "环境初始化完成！"
log_info "运行测试: pytest tests/e2e/aws/ -v"
