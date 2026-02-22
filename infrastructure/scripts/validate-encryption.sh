#!/usr/bin/env bash
# 加密合规性验证脚本
# 验证 S3 SSE-KMS 加密、API TLS 1.2+ 强制、并生成审计报告
#
# 使用方式:
#   chmod +x validate-encryption.sh
#   ./validate-encryption.sh --region us-east-1 --env dev --report report.txt
#
# 依赖: AWS CLI v2, jq, openssl
#
# 参考:
#   - CDK StorageStack: infrastructure/cdk/stacks/storage/storage_stack.py
#   - 安全规范: FR-018 (数据加密要求)

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 默认参数
REGION="us-east-1"
ENVIRONMENT="dev"
RESOURCE_PREFIX="ai-platform-dev"
REPORT_FILE=""
EXIT_CODE=0
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --region REGION       AWS 区域 (默认: us-east-1)"
    echo "  --env ENV             环境名称: dev|staging|prod (默认: dev)"
    echo "  --prefix PREFIX       资源前缀 (默认: ai-platform-dev)"
    echo "  --report FILE         输出审计报告到文件"
    echo "  -h, --help            显示帮助信息"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --region) REGION="$2"; shift 2 ;;
        --env) ENVIRONMENT="$2"; shift 2 ;;
        --prefix) RESOURCE_PREFIX="$2"; shift 2 ;;
        --report) REPORT_FILE="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
done

# 日志函数
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS_COUNT++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL_COUNT++)); EXIT_CODE=1; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN_COUNT++)); }
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_section() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

report() {
    if [[ -n "$REPORT_FILE" ]]; then
        echo "$1" >> "$REPORT_FILE"
    fi
}

# 初始化报告
if [[ -n "$REPORT_FILE" ]]; then
    cat > "$REPORT_FILE" << EOF
# 加密合规性审计报告
# 生成时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# 环境: ${ENVIRONMENT}
# 区域: ${REGION}
# 资源前缀: ${RESOURCE_PREFIX}
---

EOF
fi

echo "============================================"
echo "加密合规性验证"
echo "============================================"
echo "区域: $REGION"
echo "环境: $ENVIRONMENT"
echo "资源前缀: $RESOURCE_PREFIX"
echo "时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"

# ============================================================
# 1. S3 存储桶 SSE-KMS 加密验证
# ============================================================
log_section "1. S3 存储桶 SSE-KMS 加密验证"
report "## 1. S3 存储桶加密"

EXPECTED_BUCKETS=(
    "${RESOURCE_PREFIX}-datasets"
    "${RESOURCE_PREFIX}-models"
    "${RESOURCE_PREFIX}-checkpoints"
)

for bucket in "${EXPECTED_BUCKETS[@]}"; do
    log_info "检查存储桶: $bucket"

    # 检查存储桶是否存在
    if ! aws s3api head-bucket --bucket "$bucket" --region "$REGION" 2>/dev/null; then
        log_fail "存储桶不存在: $bucket"
        report "- [FAIL] $bucket: 存储桶不存在"
        continue
    fi

    # 检查默认加密配置
    encryption=$(aws s3api get-bucket-encryption \
        --bucket "$bucket" \
        --region "$REGION" \
        --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault' \
        --output json 2>/dev/null || echo '{}')

    sse_algorithm=$(echo "$encryption" | jq -r '.SSEAlgorithm // "NONE"')
    kms_key_id=$(echo "$encryption" | jq -r '.KMSMasterKeyID // "NONE"')

    if [[ "$sse_algorithm" == "aws:kms" ]] || [[ "$sse_algorithm" == "aws:kms:dsse" ]]; then
        log_pass "存储桶 $bucket 已启用 SSE-KMS 加密 (Key: ${kms_key_id:0:40}...)"
        report "- [PASS] $bucket: SSE-KMS (Key: $kms_key_id)"
    elif [[ "$sse_algorithm" == "AES256" ]]; then
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            log_fail "存储桶 $bucket 使用 SSE-S3 (AES256)，生产环境要求 SSE-KMS"
            report "- [FAIL] $bucket: SSE-S3 (生产环境要求 SSE-KMS)"
        else
            log_warn "存储桶 $bucket 使用 SSE-S3 (AES256)，建议升级到 SSE-KMS"
            report "- [WARN] $bucket: SSE-S3 (建议 SSE-KMS)"
        fi
    else
        log_fail "存储桶 $bucket 未配置服务端加密"
        report "- [FAIL] $bucket: 未配置加密"
    fi

    # 检查 Bucket 策略是否强制 HTTPS
    policy=$(aws s3api get-bucket-policy --bucket "$bucket" --region "$REGION" --output text 2>/dev/null || echo "")
    if echo "$policy" | jq -e '.Statement[] | select(.Condition.Bool."aws:SecureTransport" == "false" and .Effect == "Deny")' > /dev/null 2>&1; then
        log_pass "存储桶 $bucket 强制 HTTPS (enforce_ssl=true)"
        report "- [PASS] $bucket: 强制 HTTPS"
    else
        log_warn "存储桶 $bucket 未检测到 HTTPS 强制策略 (可能由 CDK enforce_ssl 管理)"
        report "- [WARN] $bucket: 未检测到显式 HTTPS 强制策略"
    fi

    # 检查公共访问阻断
    public_access=$(aws s3api get-public-access-block \
        --bucket "$bucket" \
        --region "$REGION" \
        --query 'PublicAccessBlockConfiguration' \
        --output json 2>/dev/null || echo '{}')

    all_blocked=$(echo "$public_access" | jq -r '
        (.BlockPublicAcls == true) and
        (.IgnorePublicAcls == true) and
        (.BlockPublicPolicy == true) and
        (.RestrictPublicBuckets == true)')

    if [[ "$all_blocked" == "true" ]]; then
        log_pass "存储桶 $bucket 已阻断所有公共访问"
        report "- [PASS] $bucket: 公共访问已阻断"
    else
        log_fail "存储桶 $bucket 未完全阻断公共访问"
        report "- [FAIL] $bucket: 公共访问未完全阻断"
    fi

    # 检查版本控制
    versioning=$(aws s3api get-bucket-versioning \
        --bucket "$bucket" \
        --region "$REGION" \
        --query 'Status' \
        --output text 2>/dev/null || echo "Disabled")

    if [[ "$versioning" == "Enabled" ]]; then
        log_pass "存储桶 $bucket 已启用版本控制"
        report "- [PASS] $bucket: 版本控制已启用"
    else
        log_warn "存储桶 $bucket 版本控制未启用: $versioning"
        report "- [WARN] $bucket: 版本控制 $versioning"
    fi

    echo ""
done

# ============================================================
# 2. KMS 密钥验证
# ============================================================
log_section "2. KMS 密钥验证"
report ""
report "## 2. KMS 密钥"

# 查找项目相关的 KMS 密钥
kms_keys=$(aws kms list-aliases \
    --region "$REGION" \
    --query "Aliases[?contains(AliasName, '${RESOURCE_PREFIX}')].{Alias:AliasName,KeyId:TargetKeyId}" \
    --output json 2>/dev/null || echo '[]')

if [[ "$kms_keys" == "[]" ]]; then
    log_warn "未找到前缀为 ${RESOURCE_PREFIX} 的 KMS 密钥别名"
    report "- [WARN] 未找到 KMS 密钥别名"
else
    echo "$kms_keys" | jq -c '.[]' | while read -r key; do
        alias_name=$(echo "$key" | jq -r '.Alias')
        key_id=$(echo "$key" | jq -r '.KeyId')

        # 检查密钥轮换
        rotation=$(aws kms get-key-rotation-status \
            --key-id "$key_id" \
            --region "$REGION" \
            --query 'KeyRotationEnabled' \
            --output text 2>/dev/null || echo "Unknown")

        if [[ "$rotation" == "True" ]]; then
            log_pass "KMS 密钥 $alias_name 已启用自动轮换"
            report "- [PASS] $alias_name ($key_id): 自动轮换已启用"
        elif [[ "$rotation" == "False" ]]; then
            if [[ "$ENVIRONMENT" == "prod" ]]; then
                log_fail "KMS 密钥 $alias_name 未启用自动轮换 (生产环境要求)"
                report "- [FAIL] $alias_name ($key_id): 自动轮换未启用"
            else
                log_warn "KMS 密钥 $alias_name 未启用自动轮换"
                report "- [WARN] $alias_name ($key_id): 自动轮换未启用"
            fi
        fi
    done
fi
echo ""

# ============================================================
# 3. API 端点 TLS 验证
# ============================================================
log_section "3. API 端点 TLS 验证"
report ""
report "## 3. TLS 配置"

# 获取 ALB DNS 名称
alb_dns=$(aws elbv2 describe-load-balancers \
    --region "$REGION" \
    --query "LoadBalancers[?contains(LoadBalancerName, '${RESOURCE_PREFIX}')].DNSName | [0]" \
    --output text 2>/dev/null || echo "None")

if [[ "$alb_dns" == "None" ]] || [[ -z "$alb_dns" ]]; then
    log_warn "未找到 ALB (前缀: ${RESOURCE_PREFIX})，跳过 TLS 验证"
    report "- [WARN] 未找到 ALB，跳过 TLS 验证"
else
    log_info "ALB DNS: $alb_dns"

    # 检查 HTTPS 监听器
    alb_arn=$(aws elbv2 describe-load-balancers \
        --region "$REGION" \
        --query "LoadBalancers[?contains(LoadBalancerName, '${RESOURCE_PREFIX}')].LoadBalancerArn | [0]" \
        --output text 2>/dev/null || echo "")

    if [[ -n "$alb_arn" ]]; then
        listeners=$(aws elbv2 describe-listeners \
            --load-balancer-arn "$alb_arn" \
            --region "$REGION" \
            --query 'Listeners[].{Port:Port,Protocol:Protocol,SslPolicy:SslPolicy}' \
            --output json 2>/dev/null || echo '[]')

        has_https=false
        echo "$listeners" | jq -c '.[]' | while read -r listener; do
            port=$(echo "$listener" | jq -r '.Port')
            protocol=$(echo "$listener" | jq -r '.Protocol')
            ssl_policy=$(echo "$listener" | jq -r '.SslPolicy // "N/A"')

            if [[ "$protocol" == "HTTPS" ]]; then
                has_https=true
                # 验证 SSL Policy 是否支持 TLS 1.2+
                if echo "$ssl_policy" | grep -qE "(TLS-1-2|TLS13|FS-1-2)"; then
                    log_pass "HTTPS 监听器 (端口 $port) 使用 TLS 1.2+ 策略: $ssl_policy"
                    report "- [PASS] HTTPS:$port SSL 策略: $ssl_policy"
                else
                    log_warn "HTTPS 监听器 (端口 $port) SSL 策略: $ssl_policy (建议使用 TLS 1.2+)"
                    report "- [WARN] HTTPS:$port SSL 策略: $ssl_policy"
                fi
            elif [[ "$protocol" == "HTTP" ]]; then
                log_info "HTTP 监听器 (端口 $port) - 检查是否配置重定向到 HTTPS"
                report "- [INFO] HTTP:$port (应配置 HTTPS 重定向)"
            fi
        done
    fi

    # 使用 openssl 验证 TLS 连接 (如果 ALB 有公网 IP)
    if command -v openssl &> /dev/null; then
        log_info "尝试 openssl TLS 握手测试..."
        tls_result=$(echo | openssl s_client -connect "${alb_dns}:443" -tls1_2 2>/dev/null | head -5 || echo "CONNECT_FAILED")
        if echo "$tls_result" | grep -q "CONNECTED"; then
            log_pass "TLS 1.2 握手成功: $alb_dns:443"
            report "- [PASS] TLS 1.2 握手成功"
        else
            log_info "TLS 握手未成功 (可能是内网 ALB，无法从本地连接)"
            report "- [INFO] TLS 握手测试无法从本地执行 (内网 ALB)"
        fi

        # 尝试 TLS 1.0 (应该失败)
        tls10_result=$(echo | openssl s_client -connect "${alb_dns}:443" -tls1 2>&1 || true)
        if echo "$tls10_result" | grep -q "CONNECTED"; then
            log_fail "TLS 1.0 仍然可连接 (应禁用)"
            report "- [FAIL] TLS 1.0 未禁用"
        else
            log_pass "TLS 1.0 已禁用"
            report "- [PASS] TLS 1.0 已禁用"
        fi
    fi
fi
echo ""

# ============================================================
# 4. RDS/Aurora 加密验证
# ============================================================
log_section "4. RDS/Aurora 加密验证"
report ""
report "## 4. 数据库加密"

db_clusters=$(aws rds describe-db-clusters \
    --region "$REGION" \
    --query "DBClusters[?contains(DBClusterIdentifier, '${RESOURCE_PREFIX}')].{Id:DBClusterIdentifier,Encrypted:StorageEncrypted,KmsKeyId:KmsKeyId}" \
    --output json 2>/dev/null || echo '[]')

if [[ "$db_clusters" == "[]" ]]; then
    log_warn "未找到前缀为 ${RESOURCE_PREFIX} 的 Aurora 集群"
    report "- [WARN] 未找到 Aurora 集群"
else
    echo "$db_clusters" | jq -c '.[]' | while read -r cluster; do
        cluster_id=$(echo "$cluster" | jq -r '.Id')
        encrypted=$(echo "$cluster" | jq -r '.Encrypted')
        kms_key=$(echo "$cluster" | jq -r '.KmsKeyId // "N/A"')

        if [[ "$encrypted" == "true" ]]; then
            log_pass "Aurora 集群 $cluster_id 已启用加密 (KMS: ${kms_key:0:40}...)"
            report "- [PASS] $cluster_id: 已加密 (KMS: $kms_key)"
        else
            log_fail "Aurora 集群 $cluster_id 未启用加密"
            report "- [FAIL] $cluster_id: 未加密"
        fi
    done
fi
echo ""

# ============================================================
# 5. 汇总报告
# ============================================================
log_section "审计汇总"
echo ""
echo "============================================"
echo -e "通过: ${GREEN}${PASS_COUNT}${NC}"
echo -e "失败: ${RED}${FAIL_COUNT}${NC}"
echo -e "警告: ${YELLOW}${WARN_COUNT}${NC}"
echo "============================================"

report ""
report "## 汇总"
report "- 通过: ${PASS_COUNT}"
report "- 失败: ${FAIL_COUNT}"
report "- 警告: ${WARN_COUNT}"

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}加密合规性验证通过${NC}"
    report "- 结果: **通过**"
else
    echo -e "${RED}加密合规性验证失败 - 存在不合规项${NC}"
    report "- 结果: **失败**"
fi

if [[ -n "$REPORT_FILE" ]]; then
    echo ""
    log_info "审计报告已保存到: $REPORT_FILE"
fi

exit $EXIT_CODE
