# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

## Project Overview

AWS CDK (Python) infrastructure for AI Training Platform, featuring SageMaker HyperPod with EKS orchestration for large-scale GPU training workloads.

## Common Commands

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# CDK operations
cdk synth                          # Synthesize CloudFormation templates
cdk deploy --context env=dev       # Deploy dev environment
cdk deploy --context env=staging   # Deploy staging environment
cdk deploy --context env=prod      # Deploy production environment
cdk diff                           # Show pending changes

# Deploy specific stack
cdk deploy ai-platform-dev-network --context env=dev

# Specify account/region via context
cdk deploy --context env=dev --context account=123456789012 --context region=us-west-2

# Code quality (configured in pyproject.toml)
ruff check .                       # Lint
ruff format .                      # Format
mypy .                             # Type check

# Testing
pytest                             # Run all tests
pytest -m unit                     # Run only unit tests
pytest -m integration              # Run only integration tests
pytest tests/unit/test_eks_stack.py -v                    # Run single test file
pytest tests/unit/test_eks_stack.py::test_function -v    # Run single test
pytest --cov=stacks --cov=config --cov-report=term-missing  # With coverage

# First-time deployment prerequisites
./scripts/setup_helm_chart.sh      # Download HyperPod Helm Chart
cdk bootstrap aws://ACCOUNT_ID/REGION  # Bootstrap CDK (once per account/region)
```

## Architecture

### Stack Layering (Dependency Order)

```
Layer 1 (Foundation):  NetworkStack, IamStack (parallel)
                            ↓
Layer 2 (Data):        DatabaseStack, StorageStack (parallel)
                            ↓
Layer 3a (Compute):    EksStack (EKS cluster + add-ons)
                            ↓
Layer 3b (HyperPod):   SagemakerHyperPodStack
                            ↓
Layer 3c (Add-ons):    HyperPodAddonsStack (Training Operator, Task Governance, Observability)
                            ↓
Layer 4 (Storage):     FsxLustreStack
                            ↓
Layer 5 (Ingress):     AlbStack
```

### Key Patterns

**Constants Usage**: Always use constants from `config/constants.py` instead of hardcoded strings:
```python
from config.constants import EKS_ADDON_NAMES, K8S_NAMESPACES, TIMEOUTS

# Good
addon_name = EKS_ADDON_NAMES.TRAINING_OPERATOR
namespace = K8S_NAMESPACES.KUBE_SYSTEM

# Avoid
addon_name = "amazon-sagemaker-hyperpod-training-operator"
```

**Environment Config Factory Methods**: Use factory methods for environment-specific configs:
```python
from config import get_environment_config, EnvironmentConfig

# Via factory function (recommended for app.py)
config = get_environment_config("dev", account="123456789012", region="us-east-1")

# Via class methods (for specific environments)
dev_config = EnvironmentConfig.for_dev(account="123456789012")
```

**Stack Dependencies**: Dependencies are declared via `add_dependency()` in `app.py`. When adding new stacks, ensure proper dependency ordering.

### Key Files

- `app.py` - CDK app entry point, stack instantiation and CDK Nag suppressions
- `config/environments.py` - Environment configs (dev/staging/prod) with dataclasses
- `config/constants.py` - Centralized constants (EKS Add-on names, Helm Chart config, Timeouts, etc.)
- `stacks/` - Individual stack implementations
- `custom_constructs/` - Reusable L2/L3 constructs (e.g., GpuNodeGroupConstruct)
- `utils/` - Utility modules:
  - `nag_suppressions.py` - Centralized CDK Nag suppressions
  - `tagging.py` - Standard tag application
  - `iam_helpers.py` - IAM helper functions
  - `s3_lifecycle.py` - S3 lifecycle policies
  - `outputs.py` - CloudFormation outputs helpers
- `aspects/` - CDK Aspects (tagging aspect applies standard tags to all resources)
- `tests/conftest.py` - Pytest fixtures (`dev_config`, `cdk_app`, `cdk_env`, etc.)

### Testing Patterns

Tests use `aws_cdk.assertions.Template` for CloudFormation assertions:
```python
from aws_cdk.assertions import Template
from tests.conftest import get_template

def test_something(cdk_app, dev_config, cdk_env):
    stack = MyStack(cdk_app, "test-stack", env_config=dev_config, env=cdk_env)
    template = get_template(stack)
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.has_resource_properties("AWS::S3::Bucket", {"BucketEncryption": {...}})
```

### HyperPod Deployment

The deployment flow for HyperPod with EKS:

1. **前置条件**: 首次部署前运行 `./scripts/setup_helm_chart.sh` 下载 Helm Chart
2. Deploy `EksStack` (includes automatic Helm Chart installation via `addHelmChart()`)
3. Deploy `SagemakerHyperPodStack`
4. Deploy `HyperPodAddonsStack` (Training Operator, Task Governance, Observability)

Note: The Helm Chart is bundled in `helm_charts/HyperPodHelmChart/` and deployed via CDK's `addHelmChart()` method with 15 分钟超时设置。

### HyperPod Add-ons

`HyperPodAddonsStack` provides essential Kubernetes add-ons for distributed training:

- **Training Operator**: Kubernetes operator for distributed training workloads (PyTorchJob, TFJob CRDs)
- **Task Governance**: Kueue for job queuing and resource management
- **Observability**: Prometheus + Grafana via Amazon Managed Service for monitoring

### Environment Configuration

Environments configured via `config/environments.py` with factory methods:
- `EnvironmentConfig.for_dev()` - Single NAT, min ACU 0.5 (can pause)
- `EnvironmentConfig.for_staging()` - Multi-AZ, moderate scaling
- `EnvironmentConfig.for_prod()` - Full HA, WAF enabled, higher ACU minimums

EKS Add-on versions managed via `EksAddonVersions`:
- `EksAddonVersions.for_k8s_1_32()` - Add-on versions for K8s 1.32
- `EksAddonVersions.for_k8s_1_33()` - Add-on versions for K8s 1.33 (default)

Configuration passed via CDK context: `--context env=dev`

### VPC Design

3-tier subnet architecture:
- **Public** (/20): NAT Gateways, ALB
- **PrivateApp** (/19): EKS nodes, compute - supports ~1,200+ nodes
- **PrivateData** (/20, isolated): FSx for Lustre, Aurora MySQL

### CDK Nag

Security checks via cdk-nag (enabled for staging/prod, skipped for dev). Suppressions centrally managed in `utils/nag_suppressions.py` with documented reasons.

### Resource Protection

- **dev**: `RemovalPolicy.DESTROY`, no deletion protection
- **staging**: `RemovalPolicy.DESTROY`, deletion protection enabled
- **prod**: `RemovalPolicy.RETAIN`, deletion protection enabled, termination protection on stacks
