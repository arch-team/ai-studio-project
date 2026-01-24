# E2E 测试环境配置管理方案

## 问题分析

### 当前配置管理现状

| 问题 | 严重性 | 描述 |
|------|--------|------|
| 硬编码默认凭证 | 🔴 高 | `admin123`, `test_password_123` 出现在代码中 |
| AWS 账号 ID 硬编码 | 🟡 中 | ECR 镜像 URI 包含 `763104351884` |
| Task Governance 硬编码 | 🟡 中 | namespace, queue_name, priority_class 硬编码 |
| 缺少配置示例文件 | 🟢 低 | 无 `.env.e2e.example` 参考 |
| 配置分散在多处 | 🟢 低 | conftest.py、constants.py、环境变量混用 |

### E2E 测试依赖的 AWS 环境配置

```
AWS 环境配置
├── 基础设施层
│   ├── AWS 凭证 (SSO/Profile/Keys)
│   ├── AWS Region
│   └── VPC/安全组配置
│
├── HyperPod 层
│   ├── HyperPod 集群名称
│   ├── EKS 集群连接
│   └── ECR 镜像 URI
│
├── Task Governance 层
│   ├── Cluster Scheduler Config
│   │   └── PriorityClasses (low-priority, high-priority)
│   ├── Compute Quotas
│   │   ├── Team-E2E-Low (namespace: hyperpod-ns-e2e-low)
│   │   └── Team-E2E-High (namespace: hyperpod-ns-e2e-high)
│   └── Kueue 配置
│       ├── ClusterQueue (nominal quota, borrowing limit)
│       └── Cohort (shared-pool)
│
└── 测试资源层
    ├── S3 Bucket (checkpoints)
    ├── 测试用户凭证
    └── GPU 实例配额
```

---

## 推荐方案：分层配置管理架构

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    配置加载优先级                            │
├─────────────────────────────────────────────────────────────┤
│  1. 环境变量 (最高优先级)                                    │
│     └─ CI/CD pipeline、本地开发覆盖                         │
│                                                             │
│  2. .env.e2e.{environment} 文件                             │
│     └─ .env.e2e.dev, .env.e2e.staging                       │
│                                                             │
│  3. tests/e2e/config/defaults.py (代码默认值)                │
│     └─ 仅用于单元测试 mock，不含敏感信息                     │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
backend/
├── .env.e2e.example          # 配置模板（提交到 Git）
├── .env.e2e.dev              # 开发环境配置（Git 忽略）
├── .env.e2e.staging          # Staging 环境配置（Git 忽略）
├── tests/
│   └── e2e/
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py   # Pydantic Settings 配置类
│       │   ├── defaults.py   # 非敏感默认值
│       │   └── validators.py # 配置验证器
│       ├── aws/
│       │   ├── conftest.py   # 使用 settings 替代硬编码
│       │   └── setup/
│       │       ├── __init__.py
│       │       ├── task_governance.py  # TG 配置脚本
│       │       └── kueue_config.py     # Kueue 配置脚本
│       └── README.md         # E2E 测试文档
└── scripts/
    └── e2e/
        ├── setup-env.sh      # 环境初始化脚本
        ├── verify-env.sh     # 环境验证脚本
        └── cleanup-env.sh    # 环境清理脚本
```

---

## 实施计划

### Phase 1: 配置类设计

**文件**: `tests/e2e/config/settings.py`

```python
"""E2E 测试配置管理 - Pydantic Settings 实现"""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2ETestSettings(BaseSettings):
    """E2E 测试配置类 - 集中管理所有环境配置"""

    model_config = SettingsConfigDict(
        env_file=(".env.e2e.dev", ".env.e2e"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========== AWS 基础配置 ==========
    aws_region: str = Field(default="us-east-1", description="AWS 区域")
    aws_account_id: str = Field(default="", description="AWS 账号 ID（必填）")

    # ========== HyperPod 配置 ==========
    hyperpod_cluster_name: str = Field(
        default="", description="HyperPod 集群名称（必填）"
    )
    hyperpod_eks_cluster_name: str = Field(
        default="", description="关联的 EKS 集群名称"
    )

    # ========== ECR 镜像配置 ==========
    test_image_uri: str = Field(
        default="",
        description="测试用 PyTorch 镜像 URI（可使用 {aws_account_id}, {aws_region} 占位符）"
    )
    pytorch_image_tag: str = Field(
        default="2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker",
        description="PyTorch 镜像标签"
    )

    # ========== Task Governance 配置 ==========
    # 低优先级队列
    e2e_low_namespace: str = Field(default="hyperpod-ns-e2e-low")
    e2e_low_queue_name: str = Field(default="hyperpod-ns-e2e-low-localqueue")
    e2e_low_priority_class: str = Field(default="low-priority")

    # 高优先级队列
    e2e_high_namespace: str = Field(default="hyperpod-ns-e2e-high")
    e2e_high_queue_name: str = Field(default="hyperpod-ns-e2e-high-localqueue")
    e2e_high_priority_class: str = Field(default="high-priority")

    # ========== 实例配置 ==========
    test_instance_type: str = Field(default="ml.g5.2xlarge")
    test_gpu_count: int = Field(default=1)

    # ========== S3 配置 ==========
    checkpoint_s3_bucket: str = Field(default="")
    checkpoint_s3_prefix: str = Field(default="e2e-tests/checkpoints")

    # ========== 测试控制 ==========
    e2e_read_only: bool = Field(default=True, description="只读模式（跳过写操作测试）")
    e2e_timeout: int = Field(default=600, description="总体超时（秒）")

    # ========== SLA 常量 ==========
    sla_checkpoint_save_timeout: int = Field(default=300)
    sla_pod_release_timeout: int = Field(default=30)
    sla_job_submission_timeout: int = Field(default=120)
    sla_job_status_poll_interval: int = Field(default=5)
    sla_max_preemption_count: int = Field(default=3)

    # ========== 计算属性 ==========
    @property
    def resolved_image_uri(self) -> str:
        """解析镜像 URI，替换占位符"""
        if self.test_image_uri:
            return self.test_image_uri.format(
                aws_account_id=self.aws_account_id,
                aws_region=self.aws_region,
            )
        # 使用 AWS 官方 DLC 镜像
        return (
            f"763104351884.dkr.ecr.{self.aws_region}.amazonaws.com/"
            f"pytorch-training:{self.pytorch_image_tag}"
        )

    @property
    def checkpoint_s3_path(self) -> str:
        """完整的 S3 路径"""
        return f"s3://{self.checkpoint_s3_bucket}/{self.checkpoint_s3_prefix}"

    # ========== 验证器 ==========
    @field_validator("hyperpod_cluster_name", "aws_account_id")
    @classmethod
    def validate_required_for_write_tests(cls, v: str, info) -> str:
        """验证写测试必填字段"""
        # 仅在非只读模式时强制要求
        return v


@lru_cache
def get_e2e_settings() -> E2ETestSettings:
    """获取单例配置实例"""
    return E2ETestSettings()
```

### Phase 2: 配置模板文件

**文件**: `.env.e2e.example`

```bash
# =============================================================================
# E2E 测试环境配置模板
# =============================================================================
# 使用方法：
#   1. 复制此文件为 .env.e2e.dev 或 .env.e2e.staging
#   2. 填写实际值
#   3. 运行测试：E2E_ENV=dev pytest tests/e2e/aws/ -v
# =============================================================================

# -----------------------------------------------------------------------------
# AWS 基础配置
# -----------------------------------------------------------------------------
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# -----------------------------------------------------------------------------
# HyperPod 集群配置
# -----------------------------------------------------------------------------
HYPERPOD_CLUSTER_NAME=ai-platform-dev-hyperpod
HYPERPOD_EKS_CLUSTER_NAME=ai-platform-dev-eks

# -----------------------------------------------------------------------------
# ECR 镜像配置
# -----------------------------------------------------------------------------
# 留空使用 AWS 官方 DLC 镜像，或指定自定义镜像
# TEST_IMAGE_URI={aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com/my-training:latest
PYTORCH_IMAGE_TAG=2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker

# -----------------------------------------------------------------------------
# Task Governance 配置
# -----------------------------------------------------------------------------
# 低优先级队列（用于被抢占的任务）
E2E_LOW_NAMESPACE=hyperpod-ns-e2e-low
E2E_LOW_QUEUE_NAME=hyperpod-ns-e2e-low-localqueue
E2E_LOW_PRIORITY_CLASS=low-priority

# 高优先级队列（用于抢占其他任务）
E2E_HIGH_NAMESPACE=hyperpod-ns-e2e-high
E2E_HIGH_QUEUE_NAME=hyperpod-ns-e2e-high-localqueue
E2E_HIGH_PRIORITY_CLASS=high-priority

# -----------------------------------------------------------------------------
# GPU 实例配置
# -----------------------------------------------------------------------------
TEST_INSTANCE_TYPE=ml.g5.2xlarge
TEST_GPU_COUNT=1

# -----------------------------------------------------------------------------
# S3 配置（Checkpoint 存储）
# -----------------------------------------------------------------------------
CHECKPOINT_S3_BUCKET=ai-training-checkpoints-dev
CHECKPOINT_S3_PREFIX=e2e-tests/checkpoints

# -----------------------------------------------------------------------------
# 测试控制
# -----------------------------------------------------------------------------
# 只读模式：true 跳过创建/删除操作，适合验证环境
E2E_READ_ONLY=false
# 总体超时（秒）
E2E_TIMEOUT=600

# -----------------------------------------------------------------------------
# SLA 常量（秒）
# -----------------------------------------------------------------------------
SLA_CHECKPOINT_SAVE_TIMEOUT=300
SLA_POD_RELEASE_TIMEOUT=30
SLA_JOB_SUBMISSION_TIMEOUT=120
SLA_JOB_STATUS_POLL_INTERVAL=5
SLA_MAX_PREEMPTION_COUNT=3
```

### Phase 3: 环境初始化脚本

**文件**: `scripts/e2e/setup-env.sh`

```bash
#!/bin/bash
# =============================================================================
# E2E 测试环境初始化脚本
# =============================================================================
# 功能：
#   1. 验证 AWS 凭证
#   2. 配置 EKS kubectl 上下文
#   3. 验证/创建 Task Governance 配置
#   4. 验证 Kueue ClusterQueue 配置
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# -----------------------------------------------------------------------------
# 1. 加载配置
# -----------------------------------------------------------------------------
ENV_FILE="${E2E_ENV:-.env.e2e.dev}"
if [[ -f "backend/$ENV_FILE" ]]; then
    log_info "加载配置文件: backend/$ENV_FILE"
    source "backend/$ENV_FILE"
else
    log_error "配置文件不存在: backend/$ENV_FILE"
    log_info "请先创建配置文件: cp backend/.env.e2e.example backend/$ENV_FILE"
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. 验证 AWS 凭证
# -----------------------------------------------------------------------------
log_info "验证 AWS 凭证..."
if ! aws sts get-caller-identity &>/dev/null; then
    log_error "AWS 凭证无效，请先登录："
    log_info "  aws sso login --profile your-profile"
    log_info "  或设置环境变量 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY"
    exit 1
fi
CALLER_IDENTITY=$(aws sts get-caller-identity --output json)
log_info "当前身份: $(echo $CALLER_IDENTITY | jq -r '.Arn')"

# -----------------------------------------------------------------------------
# 3. 配置 EKS kubectl 上下文
# -----------------------------------------------------------------------------
log_info "配置 EKS kubectl 上下文..."
aws eks update-kubeconfig \
    --region "$AWS_REGION" \
    --name "$HYPERPOD_EKS_CLUSTER_NAME"

# 切换到 HyperPod 上下文
HYPERPOD_CONTEXT="${HYPERPOD_CLUSTER_NAME}"
if kubectl config get-contexts "$HYPERPOD_CONTEXT" &>/dev/null; then
    kubectl config use-context "$HYPERPOD_CONTEXT"
    log_info "已切换到上下文: $HYPERPOD_CONTEXT"
else
    log_warn "上下文 $HYPERPOD_CONTEXT 不存在，使用当前上下文"
fi

# -----------------------------------------------------------------------------
# 4. 验证 Task Governance 配置
# -----------------------------------------------------------------------------
log_info "验证 Task Governance 配置..."

# 检查 Cluster Scheduler Config
SCHEDULER_CONFIG=$(aws sagemaker describe-cluster-scheduler-config \
    --cluster-identifier "arn:aws:sagemaker:${AWS_REGION}:${AWS_ACCOUNT_ID}:cluster/${HYPERPOD_CLUSTER_NAME}" \
    --output json 2>/dev/null || echo "{}")

if [[ $(echo "$SCHEDULER_CONFIG" | jq -r '.ClusterSchedulerConfigArn // empty') ]]; then
    log_info "✅ Cluster Scheduler Config 已配置"
    # 显示 PriorityClasses
    echo "$SCHEDULER_CONFIG" | jq '.SchedulerConfig.PriorityClasses'
else
    log_warn "⚠️ Cluster Scheduler Config 未配置"
    log_info "请参考文档配置 Task Governance"
fi

# 检查 Compute Quotas
log_info "检查 Compute Quotas..."
QUOTAS=$(aws sagemaker list-compute-quotas \
    --cluster-arn "arn:aws:sagemaker:${AWS_REGION}:${AWS_ACCOUNT_ID}:cluster/${HYPERPOD_CLUSTER_NAME}" \
    --output json 2>/dev/null || echo "{}")

echo "$QUOTAS" | jq '.ComputeQuotaSummaries[] | {Name: .Name, Namespace: .TargetEntityConfig.TeamName}'

# -----------------------------------------------------------------------------
# 5. 验证 Kueue ClusterQueue 配置
# -----------------------------------------------------------------------------
log_info "验证 Kueue ClusterQueue 配置..."
kubectl get clusterqueues -o custom-columns=NAME:.metadata.name,COHORT:.spec.cohort,NOMINAL:.spec.resourceGroups

# 检查抢占配置
LOW_QUEUE_NOMINAL=$(kubectl get clusterqueue "${E2E_LOW_QUEUE_NAME%-localqueue}" \
    -o jsonpath='{.spec.resourceGroups[0].flavors[0].resources[0].nominalQuota}' 2>/dev/null || echo "N/A")
HIGH_QUEUE_NOMINAL=$(kubectl get clusterqueue "${E2E_HIGH_QUEUE_NAME%-localqueue}" \
    -o jsonpath='{.spec.resourceGroups[0].flavors[0].resources[0].nominalQuota}' 2>/dev/null || echo "N/A")

log_info "低优先级队列 nominal quota: $LOW_QUEUE_NOMINAL"
log_info "高优先级队列 nominal quota: $HIGH_QUEUE_NOMINAL"

# 验证抢占配置是否正确
if [[ "$LOW_QUEUE_NOMINAL" == "0" && "$HIGH_QUEUE_NOMINAL" == "1" ]]; then
    log_info "✅ 抢占配置正确：低=0, 高=1"
else
    log_warn "⚠️ 抢占配置可能需要调整"
    log_info "正确配置：低优先级 nominal=0, borrow=1; 高优先级 nominal=1, borrow=0"
fi

# -----------------------------------------------------------------------------
# 6. 输出摘要
# -----------------------------------------------------------------------------
echo ""
log_info "========== 环境配置摘要 =========="
echo "AWS Region:        $AWS_REGION"
echo "AWS Account:       $AWS_ACCOUNT_ID"
echo "HyperPod Cluster:  $HYPERPOD_CLUSTER_NAME"
echo "EKS Cluster:       $HYPERPOD_EKS_CLUSTER_NAME"
echo "Low Priority NS:   $E2E_LOW_NAMESPACE"
echo "High Priority NS:  $E2E_HIGH_NAMESPACE"
echo "Read-Only Mode:    $E2E_READ_ONLY"
log_info "=================================="

log_info "环境初始化完成！运行测试："
log_info "  pytest tests/e2e/aws/ -v -m 'not slow'"
```

### Phase 4: 配置验证脚本

**文件**: `scripts/e2e/verify-env.sh`

```bash
#!/bin/bash
# E2E 环境验证脚本 - 快速检查环境是否就绪

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASSED=0
FAILED=0

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

echo "🔍 E2E 环境验证"
echo "=================="

check "AWS 凭证" "aws sts get-caller-identity"
check "kubectl 连接" "kubectl cluster-info"
check "HyperPod SDK" "python -c 'from hyperpod_sdk import HyperPodPytorchJob'"
check "配置文件存在" "test -f backend/.env.e2e.dev || test -f backend/.env.e2e"
check "低优先级 namespace" "kubectl get namespace ${E2E_LOW_NAMESPACE:-hyperpod-ns-e2e-low}"
check "高优先级 namespace" "kubectl get namespace ${E2E_HIGH_NAMESPACE:-hyperpod-ns-e2e-high}"
check "ClusterQueue 存在" "kubectl get clusterqueues"
check "PriorityClass 存在" "kubectl get priorityclasses | grep -E 'low-priority|high-priority'"

echo "=================="
echo "通过: $PASSED / 失败: $FAILED"

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}环境未就绪，请运行 setup-env.sh${NC}"
    exit 1
fi
echo -e "${GREEN}环境就绪！${NC}"
```

### Phase 5: 更新 conftest.py 使用新配置

**修改**: `tests/e2e/aws/conftest.py`

```python
# 替换硬编码配置
from tests.e2e.config.settings import get_e2e_settings

settings = get_e2e_settings()

# 使用 settings 替代硬编码
@pytest.fixture(scope="session")
def aws_region() -> str:
    return settings.aws_region

@pytest.fixture(scope="session")
def hyperpod_cluster_name() -> str:
    return settings.hyperpod_cluster_name

@pytest.fixture
def low_priority_job_config() -> dict[str, Any]:
    return {
        "job_name": f"e2e-low-priority-{int(time.time() * 1000) % 10000000000}",
        "namespace": settings.e2e_low_namespace,
        "queue_name": settings.e2e_low_queue_name,
        "priority_class": settings.e2e_low_priority_class,
        "image_uri": settings.resolved_image_uri,
        "instance_type": settings.test_instance_type,
        "gpu_count": settings.test_gpu_count,
        # ...其他配置
    }
```

---

## 关键文件清单

| 文件 | 状态 | 职责 |
|------|------|------|
| `tests/e2e/config/settings.py` | 新增 | Pydantic 配置类 |
| `tests/e2e/config/defaults.py` | 新增 | 非敏感默认值 |
| `.env.e2e.example` | 新增 | 配置模板 |
| `.env.e2e.dev` | 新增 | 开发环境配置（Git 忽略）|
| `scripts/e2e/setup-env.sh` | 新增 | 环境初始化脚本 |
| `scripts/e2e/verify-env.sh` | 新增 | 环境验证脚本 |
| `tests/e2e/aws/conftest.py` | 修改 | 使用 settings 替代硬编码 |
| `.gitignore` | 修改 | 添加 `.env.e2e.*` (排除 example) |

---

## 验证步骤

### 1. 配置文件设置

```bash
# 复制模板
cp backend/.env.e2e.example backend/.env.e2e.dev

# 编辑配置
vim backend/.env.e2e.dev
```

### 2. 环境初始化

```bash
# 初始化环境
./scripts/e2e/setup-env.sh

# 快速验证
./scripts/e2e/verify-env.sh
```

### 3. 运行测试

```bash
# 使用开发环境配置
E2E_ENV=.env.e2e.dev pytest tests/e2e/aws/test_e2e_preemption_sla.py -v

# 或指定配置文件
pytest tests/e2e/aws/ -v --env-file=.env.e2e.staging
```

---

## 方案优势

| 特性 | 说明 |
|------|------|
| **类型安全** | Pydantic 自动验证配置类型 |
| **环境隔离** | 支持 dev/staging/prod 多环境 |
| **敏感信息保护** | 凭证不进入 Git，使用环境变量 |
| **自动补全** | IDE 支持配置项自动补全 |
| **配置验证** | setup 脚本自动检查环境就绪状态 |
| **文档化** | 配置模板包含完整注释说明 |
