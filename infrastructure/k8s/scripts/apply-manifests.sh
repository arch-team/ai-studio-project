#!/usr/bin/env bash
# 统一部署 K8s Manifests 到目标环境
# 用法: bash apply-manifests.sh <env> [--dry-run]
# 示例:
#   bash apply-manifests.sh dev --dry-run   # 预览变更
#   bash apply-manifests.sh dev             # 应用变更

set -euo pipefail

ENV="${1:?用法: apply-manifests.sh <env> [--dry-run]}"
DRY_RUN="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_ROOT="$(dirname "${SCRIPT_DIR}")"
OVERLAY_DIR="${K8S_ROOT}/overlays/${ENV}"

# 验证环境目录存在
if [ ! -d "${OVERLAY_DIR}" ]; then
    echo "错误: 环境目录不存在: ${OVERLAY_DIR}"
    echo "可用环境: dev, staging, prod"
    exit 1
fi

echo "=== AI Training Platform K8s Deployment ==="
echo "环境: ${ENV}"
echo "Overlay: ${OVERLAY_DIR}"
echo ""

# Step 1: Kustomize build 预览
echo "--- Step 1: 构建 Kustomize 配置 ---"
kubectl kustomize "${OVERLAY_DIR}"

echo ""
echo "--- Step 2: 应用配置 ---"

if [ "${DRY_RUN}" = "--dry-run" ]; then
    echo "(Dry-run 模式)"
    kubectl apply --dry-run=client -k "${OVERLAY_DIR}"
else
    kubectl apply -k "${OVERLAY_DIR}"
    echo ""
    echo "部署完成! 环境: ${ENV}"
fi
