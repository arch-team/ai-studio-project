#!/usr/bin/env bash
# 从 AWS Secrets Manager 读取 Aurora 凭证并创建 K8s Secret
# 用法: bash infrastructure/scripts/create-backend-secret.sh [namespace]

set -euo pipefail

NAMESPACE="${1:-ai-platform}"
SECRET_NAME="backend-secrets"
REGION="us-east-1"
SM_SECRET_ID="ai-platform-dev/aurora/credentials"
DB_HOST="ai-platform-dev-aurora-proxy.proxy-cqm7um8tgaji.us-east-1.rds.amazonaws.com"
DB_PORT="3306"

echo "=== 从 Secrets Manager 获取数据库凭证 ==="
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "${SM_SECRET_ID}" \
  --region "${REGION}" \
  --query 'SecretString' --output text)

DB_USER=$(echo "${SECRET_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])")
DB_PASS=$(echo "${SECRET_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")
DB_NAME=$(echo "${SECRET_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('dbname','ai_training'))")

DATABASE_URL="mysql+aiomysql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
SECRET_KEY=$(openssl rand -hex 32)

echo "=== 创建/更新 K8s Secret: ${SECRET_NAME} ==="
kubectl create secret generic "${SECRET_NAME}" \
  --namespace "${NAMESPACE}" \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=SECRET_KEY="${SECRET_KEY}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "=== Secret ${SECRET_NAME} 创建成功 ==="
kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}"
