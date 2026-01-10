# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
Layer 1 (Foundation):  NetworkStack → IamStack
                            ↓
Layer 2 (Data):        DatabaseStack, StorageStack
                            ↓
Layer 3a (Compute):    EksStack (EKS cluster + add-ons)
                            ↓
        [Manual Step: Install HyperPod Helm Chart]
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

### Two-Phase HyperPod Deployment

HyperPod requires Helm chart installation between EKS and HyperPod stack deployment:

1. Deploy `EksStack` first
2. Configure kubectl and install HyperPod Helm Chart:
   ```bash
   git clone https://github.com/aws/sagemaker-hyperpod-cli.git
   cd sagemaker-hyperpod-cli/helm_chart
   helm dependencies update HyperPodHelmChart
   helm install hyperpod-dependencies HyperPodHelmChart --namespace kube-system
   ```
3. Deploy `SagemakerHyperPodStack`

The legacy `HyperPodStack` combines both but doesn't support proper Helm sequencing.

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
