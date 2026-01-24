#!/bin/bash
# =============================================================================
# E2E 环境验证脚本 - 快速检查环境是否就绪
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
ENV_FILE="${E2E_ENV:-.env.e2e.dev}"
if [[ -f "$BACKEND_DIR/$ENV_FILE" ]]; then
    set -a
    source "$BACKEND_DIR/$ENV_FILE"
    set +a
elif [[ -f "$BACKEND_DIR/.env.e2e" ]]; then
    set -a
    source "$BACKEND_DIR/.env.e2e"
    set +a
fi

echo ""
echo "📋 必要条件"
echo "------------"

check "AWS CLI 已安装" "command -v aws"
check "AWS 凭证有效" "aws sts get-caller-identity"
check "kubectl 已安装" "command -v kubectl"
check "kubectl 连接正常" "kubectl cluster-info"
check "配置文件存在" "test -f '$BACKEND_DIR/.env.e2e.dev' || test -f '$BACKEND_DIR/.env.e2e'"

echo ""
echo "📦 Python 依赖"
echo "--------------"

check "pytest 已安装" "python -c 'import pytest'"
check "pydantic-settings 已安装" "python -c 'import pydantic_settings'"
check "boto3 已安装" "python -c 'import boto3'"
warn_check "HyperPod SDK 已安装" "python -c 'from hyperpod_sdk import HyperPodPytorchJob'"

echo ""
echo "🎯 Task Governance"
echo "------------------"

LOW_NS="${E2E_LOW_NAMESPACE:-hyperpod-ns-e2e-low}"
HIGH_NS="${E2E_HIGH_NAMESPACE:-hyperpod-ns-e2e-high}"

warn_check "低优先级 namespace: $LOW_NS" "kubectl get namespace '$LOW_NS'"
warn_check "高优先级 namespace: $HIGH_NS" "kubectl get namespace '$HIGH_NS'"
warn_check "ClusterQueue 存在" "kubectl get clusterqueues 2>/dev/null | grep -q ."
warn_check "PriorityClass 存在" "kubectl get priorityclasses 2>/dev/null | grep -E 'low-priority|high-priority'"

echo ""
echo "=================="
echo -e "通过: ${GREEN}$PASSED${NC} | 失败: ${RED}$FAILED${NC} | 警告: ${YELLOW}$WARNINGS${NC}"

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo -e "${RED}环境未就绪${NC}"
    echo "请运行 setup-env.sh 初始化环境"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}环境基本就绪${NC}（部分可选组件未配置）"
    echo "可以运行只读测试: pytest tests/e2e/aws/ -v -m 'not slow'"
    exit 0
else
    echo ""
    echo -e "${GREEN}环境完全就绪！${NC}"
    echo "运行测试: pytest tests/e2e/aws/ -v"
    exit 0
fi
