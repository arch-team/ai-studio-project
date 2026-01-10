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
Layer 3a (Compute):    EksStack (EKS cluster + add-ons + Helm Chart auto-install)
                            ↓
Layer 3b (HyperPod):   SagemakerHyperPodStack
                            ↓
Layer 4 (Storage):     FsxLustreStack
                            ↓
Layer 5 (Ingress):     AlbStack
```

### Key Files

- `app.py` - CDK app entry point, stack instantiation and CDK Nag suppressions
- `config/environments.py` - Environment configs (dev/staging/prod) with dataclasses
- `stacks/` - Individual stack implementations
- `custom_constructs/` - Reusable L2/L3 constructs (e.g., GpuNodeGroupConstruct)

### HyperPod Deployment

EksStack automatically installs the HyperPod Helm Chart during deployment. The deployment flow is:

1. **前置条件**: 首次部署前运行 `./scripts/setup_helm_chart.sh` 下载 Helm Chart
2. Deploy `EksStack` (includes automatic Helm Chart installation via `addHelmChart()`)
3. Deploy `SagemakerHyperPodStack`

Note: The Helm Chart is bundled in `helm_charts/HyperPodHelmChart/` and deployed via CDK's `addHelmChart()` method with 15 分钟超时设置。

### Environment Configuration

Environments configured via `config/environments.py` with factory methods:
- `EnvironmentConfig.for_dev()` - Single NAT, min ACU 0.5 (can pause)
- `EnvironmentConfig.for_staging()` - Multi-AZ, moderate scaling
- `EnvironmentConfig.for_prod()` - Full HA, WAF enabled, higher ACU minimums

Configuration passed via CDK context: `--context env=dev`

### VPC Design

3-tier subnet architecture:
- **Public** (/20): NAT Gateways, ALB
- **PrivateApp** (/19): EKS nodes, compute - supports ~1,200+ nodes
- **PrivateData** (/20, isolated): FSx for Lustre, Aurora MySQL

### CDK Nag

Security checks via cdk-nag (enabled for staging/prod, skipped for dev). Suppressions defined in `app.py` with documented reasons.
