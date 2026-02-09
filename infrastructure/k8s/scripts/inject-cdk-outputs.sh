#!/usr/bin/env bash
# 从 CDK CloudFormation Outputs 注入变量到 .env 文件
# 用法: bash inject-cdk-outputs.sh <env>
# 示例: bash inject-cdk-outputs.sh dev

set -euo pipefail

ENV="${1:?用法: inject-cdk-outputs.sh <env> (dev|staging|prod)}"
STACK_PREFIX="ai-platform-${ENV}"
OUTPUT_FILE="infrastructure/k8s/overlays/${ENV}/.env"

echo "# 从 CDK CloudFormation Outputs 自动生成" > "${OUTPUT_FILE}"
echo "# 生成时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${OUTPUT_FILE}"
echo "" >> "${OUTPUT_FILE}"

# 从各 Stack 提取 Outputs
declare -a STACKS=(
    "${STACK_PREFIX}-network"
    "${STACK_PREFIX}-eks"
    "${STACK_PREFIX}-storage"
    "${STACK_PREFIX}-database"
    "${STACK_PREFIX}-fsx"
)

for stack in "${STACKS[@]}"; do
    echo "# --- ${stack} ---" >> "${OUTPUT_FILE}"

    # 获取 Stack Outputs (JSON 格式)
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "${stack}" \
        --query 'Stacks[0].Outputs' \
        --output json 2>/dev/null || echo "[]")

    if [ "${outputs}" = "[]" ] || [ "${outputs}" = "null" ]; then
        echo "# (无输出或 Stack 不存在)" >> "${OUTPUT_FILE}"
        continue
    fi

    # 解析每个 Output
    echo "${outputs}" | jq -r '.[] | "\(.OutputKey)=\(.OutputValue)"' >> "${OUTPUT_FILE}"
    echo "" >> "${OUTPUT_FILE}"
done

echo "已生成: ${OUTPUT_FILE}"
