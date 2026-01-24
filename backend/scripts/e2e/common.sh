#!/bin/bash
# =============================================================================
# E2E 脚本共享函数库
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# 获取脚本目录
get_script_dir() {
    echo "$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
}

# 获取后端目录
get_backend_dir() {
    local script_dir=$(get_script_dir)
    echo "$(cd "$script_dir/../.." && pwd)"
}

# 加载环境配置
load_env_config() {
    local backend_dir=$(get_backend_dir)
    local env_file="${E2E_ENV:-.env.e2e.dev}"

    for file in "$backend_dir/$env_file" "$backend_dir/.env.e2e"; do
        if [[ -f "$file" ]]; then
            log_info "加载配置: $file"
            set -a
            source "$file"
            set +a
            return 0
        fi
    done

    log_error "配置文件不存在"
    log_info "请创建: cp $backend_dir/.env.e2e.example $backend_dir/.env.e2e.dev"
    return 1
}

# 检查 AWS 凭证
check_aws_credentials() {
    if ! command -v aws &>/dev/null; then
        log_error "AWS CLI 未安装"
        return 1
    fi

    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS 凭证无效"
        log_info "请先登录: aws sso login --profile your-profile"
        return 1
    fi

    return 0
}

# 获取 AWS 账号信息
get_aws_account_info() {
    local caller_identity=$(aws sts get-caller-identity --output json 2>/dev/null)
    if [[ -n "$caller_identity" ]]; then
        echo "$caller_identity" | jq -r '.Account'
    fi
}

# 检查 kubectl
check_kubectl() {
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl 未安装"
        return 1
    fi

    if kubectl cluster-info &>/dev/null; then
        return 0
    else
        log_warn "kubectl 无法连接到集群"
        return 1
    fi
}

# 获取集群 ARN
get_cluster_arn() {
    local cluster_name="$1"
    local region="${AWS_REGION:-us-east-1}"
    local account=$(get_aws_account_info)

    if [[ -n "$cluster_name" && -n "$account" ]]; then
        echo "arn:aws:sagemaker:${region}:${account}:cluster/${cluster_name}"
    fi
}