#!/bin/bash
# =============================================================================
# E2E 环境快速验证脚本
# =============================================================================

set -euo pipefail

# 导入共享函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 计数器
PASSED=0
FAILED=0
WARNINGS=0

# 检查函数
check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}✅${NC} $name"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $name"
        ((FAILED++))
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}✅${NC} $name"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️${NC}  $name (可选)"
        ((WARNINGS++))
    fi
}

echo "🔍 E2E 环境验证"
echo "=================="

# 加载配置
load_env_config 2>/dev/null || true

echo ""
echo "📋 必要条件"
echo "------------"

check "AWS CLI 已安装" "command -v aws"
check "AWS 凭证有效" "aws sts get-caller-identity"
check "kubectl 已安装" "command -v kubectl"
check "kubectl 连接" "kubectl cluster-info"
check "配置文件" "test -f '$(get_backend_dir)/.env.e2e.dev' || test -f '$(get_backend_dir)/.env.e2e'"

echo ""
echo "📦 Python 依赖"
echo "--------------"

check "pytest" "python -c 'import pytest'"
check "pydantic-settings" "python -c 'import pydantic_settings'"
check "boto3" "python -c 'import boto3'"
warn_check "HyperPod SDK" "python -c 'from hyperpod_sdk import HyperPodPytorchJob'"

echo ""
echo "🎯 Task Governance"
echo "------------------"

LOW_NS="${E2E_LOW_NAMESPACE:-hyperpod-ns-e2e-low}"
HIGH_NS="${E2E_HIGH_NAMESPACE:-hyperpod-ns-e2e-high}"

warn_check "低优先级 NS: $LOW_NS" "kubectl get namespace '$LOW_NS'"
warn_check "高优先级 NS: $HIGH_NS" "kubectl get namespace '$HIGH_NS'"
warn_check "ClusterQueue" "kubectl get clusterqueues 2>/dev/null | grep -q ."
warn_check "PriorityClass" "kubectl get priorityclasses 2>/dev/null | grep -E 'low-priority|high-priority'"

echo ""
echo "=================="
echo -e "✅ ${GREEN}$PASSED${NC} | ❌ ${RED}$FAILED${NC} | ⚠️  ${YELLOW}$WARNINGS${NC}"

if [[ $FAILED -gt 0 ]]; then
    echo -e "\n${RED}环境未就绪${NC}"
    echo "运行: ./scripts/e2e/setup-env.sh"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "\n${YELLOW}环境基本就绪${NC}"
    echo "运行: pytest tests/e2e/aws/ -v"
    exit 0
else
    echo -e "\n${GREEN}环境完全就绪！${NC}"
    echo "运行: pytest tests/e2e/aws/ -v"
    exit 0
fi
