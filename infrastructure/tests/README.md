# Infrastructure Tests

HyperPod 基础设施验证测试套件，用于验证 EKS 集群、HyperPod Add-ons、FSx 存储和网络连接。

## 目录结构

```
tests/
├── README.md                    # 本文档
├── __init__.py                  # Python 包初始化
├── conftest.py                  # Pytest fixtures (CDK + 集成测试)
├── run-validation-suite.sh      # 主验证入口脚本
│
├── unit/                        # 单元测试 (CDK 配置验证)
│   ├── __init__.py
│   └── test_config.py           # CDK 配置测试
│
├── integration/                 # 集成测试 (实际基础设施验证)
│   ├── __init__.py
│   └── test_infrastructure.py   # K8s 集群和 HyperPod 验证
│
├── scripts/                     # Shell 验证脚本
│   ├── validate-infrastructure.sh   # 完整基础设施验证
│   ├── verify-hyperpod-addons.sh    # HyperPod Add-ons 验证
│   ├── quick-validate.sh            # 快速验证脚本
│   └── fsx-performance-test.sh      # FSx 性能测试
│
├── manifests/                   # K8s 测试资源
│   ├── test-pytorchjob.yaml     # PyTorchJob 功能测试
│   └── test-kueue.yaml          # Kueue 调度测试
│
└── reports/                     # 测试报告输出目录
    └── .gitkeep
```

## 快速开始

### 前置条件

- kubectl 已配置集群凭证
- AWS CLI 已配置适当权限
- Python 3.11+ (pytest 测试)
- 已安装 jq, curl, openssl

### 运行测试

#### 1. 快速验证 (推荐)

```bash
# 运行快速基础设施检查
./run-validation-suite.sh --quick

# 或直接使用快速验证脚本
./scripts/quick-validate.sh
```

#### 2. 完整验证

```bash
# 运行所有验证套件
./run-validation-suite.sh --full
```

#### 3. 仅 Pytest 测试

```bash
# 运行所有 Python 测试
./run-validation-suite.sh --pytest-only

# 或使用 pytest 直接运行
cd infrastructure/tests
pytest -v                           # 运行所有测试
pytest unit/ -v                     # 仅单元测试
pytest integration/ -v              # 仅集成测试
pytest -v -k "cluster"              # 按关键字筛选
pytest -v -m "not slow"             # 排除慢测试
```

#### 4. K8s 资源测试

```bash
# 测试 PyTorchJob
kubectl apply -f manifests/test-pytorchjob.yaml
kubectl get pytorchjob -n training-jobs -w

# 测试 Kueue
kubectl apply -f manifests/test-kueue.yaml
kubectl get clusterqueue,localqueue -A

# 清理
kubectl delete -f manifests/test-pytorchjob.yaml
kubectl delete -f manifests/test-kueue.yaml
```

## 测试套件说明

### 单元测试 (unit/)

| 测试文件 | 描述 |
|----------|------|
| test_config.py | CDK 环境配置验证 |

### 集成测试 (integration/)

| 测试类 | 描述 |
|--------|------|
| TestClusterHealth | EKS 集群健康检查 |
| TestGPUNodes | GPU 节点和 NVIDIA 驱动验证 |
| TestHyperPodAddons | Training Operator, Kueue, 监控组件 |
| TestFSxStorage | FSx CSI 驱动和存储类 |
| TestNetworkConnectivity | DNS、网络、S3 端点连接 |
| TestTLSHTTPS | ALB、TLS 配置验证 |
| TestIntegration | PyTorchJob 提交端到端测试 |

### Shell 脚本 (scripts/)

| 脚本 | 描述 |
|------|------|
| validate-infrastructure.sh | 完整基础设施验证 |
| verify-hyperpod-addons.sh | HyperPod Add-ons 专项验证 |
| quick-validate.sh | 快速健康检查 |
| fsx-performance-test.sh | FSx 性能基准测试 (≥5GB/s) |

## 测试报告

测试报告输出到 `reports/` 目录：

```
reports/
├── infrastructure-validation-report-YYYYMMDD_HHMMSS.md
├── pytest-YYYYMMDD_HHMMSS.log
├── cluster-health-YYYYMMDD_HHMMSS.log
└── hyperpod-addons-YYYYMMDD_HHMMSS.log
```

## 环境变量

可通过环境变量自定义测试配置：

```bash
export CLUSTER_NAME="ai-platform-hyperpod"
export NAMESPACE_TRAINING="training-jobs"
export NAMESPACE_MONITORING="hyperpod-observability"
export NAMESPACE_KUEUE="kueue-system"
export AWS_REGION="us-east-1"
```

## 参考文档

- tasks.md T008g - HyperPod 基础设施验证测试
- spec.md FR-007 - FSx 性能要求 (≥5GB/s)
- spec.md FR-004 - 任务优先级配置
