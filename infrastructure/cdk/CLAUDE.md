# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **回复语言要求参见根目录 `CLAUDE.md`**

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

# Specify account/region via context
cdk deploy --context env=dev --context account=123456789012 --context region=us-west-2

# Code quality (configured in pyproject.toml)
ruff check .                       # Lint
ruff format .                      # Format
mypy .                             # Type check
pytest                             # Run tests
pytest -m unit                     # Run only unit tests
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

### Key Files

- `app.py` - CDK app entry point, stack instantiation and CDK Nag suppressions
- `config/environments.py` - Environment configs (dev/staging/prod) with dataclasses
- `config/constants.py` - Centralized constants (EKS Add-on names, Helm Chart config, Timeouts, etc.)
- `stacks/` - Stack implementations organized by deployment layer:
  - `foundation/` - Layer 1: NetworkStack, IamStack
  - `data/` - Layer 2: DatabaseStack, StorageStack, FsxLustreStack
  - `compute/` - Layer 3: EksStack, SagemakerHyperPodStack, HyperPodAddonsStack
  - `networking/` - Layer 4: AlbStack
- `cdk_constructs/` - Reusable L2/L3 constructs (e.g., GpuNodeGroupConstruct)
- `utils/` - Utility modules:
  - `nag_suppressions.py` - Centralized CDK Nag suppressions
  - `tagging.py` - Standard tag application
  - `iam_helpers.py` - IAM helper functions
  - `s3_lifecycle.py` - S3 lifecycle policies
  - `outputs.py` - CloudFormation outputs helpers
- `aspects/` - CDK Aspects (e.g., tagging aspect)
- `resources/` - Static resources:
  - `helm_charts/` - HyperPod Helm Charts
  - `scripts/` - Setup and deployment scripts

### HyperPod Deployment

The deployment flow for HyperPod with EKS:

1. **前置条件**: 首次部署前运行 `./resources/scripts/setup_helm_chart.sh` 下载 Helm Chart
2. Deploy `EksStack` (includes automatic Helm Chart installation via `addHelmChart()`)
3. Deploy `SagemakerHyperPodStack`
4. Deploy `HyperPodAddonsStack` (Training Operator, Task Governance, Observability)

Note: The Helm Chart is bundled in `resources/helm_charts/HyperPodHelmChart/` and deployed via CDK's `addHelmChart()` method with 15 分钟超时设置。

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
- `EksAddonVersions.for_k8s_1_33()` - Add-on versions for K8s 1.33

Configuration passed via CDK context: `--context env=dev`

### VPC Design

3-tier subnet architecture:
- **Public** (/20): NAT Gateways, ALB
- **PrivateApp** (/19): EKS nodes, compute - supports ~1,200+ nodes
- **PrivateData** (/20, isolated): FSx for Lustre, Aurora MySQL

### CDK Nag

Security checks via cdk-nag (enabled for staging/prod, skipped for dev). Suppressions centrally managed in `utils/nag_suppressions.py` with documented reasons.
