# Infrastructure 工程目录结构与架构设计改进方案

## Context

AI Training Platform 的 infrastructure 子项目基于 AWS CDK (Python) 构建了 5 层 Stack 分层架构，支撑 SageMaker HyperPod + EKS 的企业级 AI 训练平台。经过全面审查，项目在架构设计、配置管理和文档规范方面表现优秀（评分 3.75/5），但在以下方面存在改进空间：

1. **目录与分层不一致**: FsxStack 物理位于 `stacks/data/` 但逻辑上是 L4（依赖 L3 EKS）
2. **DRY 违规**: IAM 角色创建逻辑分散在 EksStack 内联方法、iam_helpers 工具函数、IamStack 中
3. **安全缺陷**: Dev 环境完全跳过 CDK Nag 检查，VPC Endpoint 安全组过于宽泛
4. **功能缺失**: Observability Stack 被禁用、缺少 K8s RBAC/PSA manifest、无 Spot 实例支持
5. **K8s manifest 无环境管理**: 使用 `${VARIABLE}` 占位符但无统一注入机制
6. **测试不足**: 缺少 Snapshot 测试和 utils/ 模块的独立测试

本方案分 3 个阶段实施完整改进。

---

## Phase 1: 基础重构与安全加固

### 1.1 目录结构重组 — 新建 `stacks/storage/`

**操作**: 将存储相关 Stack 从 `data/` 迁移到新的 `storage/` 目录

```
stacks/
├── foundation/     # L1 (不变)
├── data/           # L2: 仅保留 DatabaseStack
├── compute/        # L3 (不变)
├── storage/        # 新建: StorageStack + FsxLustreStack
│   ├── __init__.py
│   ├── storage_stack.py    ← 从 data/ 迁移
│   └── fsx_stack.py        ← 从 data/ 迁移
└── networking/     # L5 (不变)
```

**修改文件清单**:

| 文件 | 操作 |
|------|------|
| `stacks/storage/__init__.py` | 新建，导出 StorageStack, FsxLustreStack |
| `stacks/data/storage_stack.py` | 移动到 `stacks/storage/` |
| `stacks/data/fsx_stack.py` | 移动到 `stacks/storage/` |
| `stacks/data/__init__.py` | 移除 StorageStack, FsxLustreStack 导出 |
| `stacks/__init__.py` | 更新导入路径，从 `.storage` 导入 |
| `app.py` | 无需修改（通过 `stacks` 顶层 `__init__.py` 导入） |
| `.claude/rules/architecture.md` | 更新目录职责表和分层说明 |

### 1.2 CDK Nag 全环境启用

**问题**: `app.py:222` — `if env_config.name.value != "dev":` 完全跳过 dev CDK Nag

**修改文件**:

- `app.py` — 移除 dev 条件判断，所有环境启用 CDK Nag:
  ```python
  # 修改前 (app.py:222-223)
  if env_config.name.value != "dev":
      cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

  # 修改后
  cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
  ```

- `utils/nag_suppressions.py` — 在 `STACK_SPECIFIC_SUPPRESSIONS` 中补充 dev 环境需要的合理抑制规则（已有的 suppressions 覆盖大部分场景，可能需要少量补充）

### 1.3 VPC Endpoint 安全组加固

**问题**: `network_stack.py` 中 VPC Endpoint 安全组允许整个 VPC CIDR (`10.0.0.0/16`) 访问

**修改文件**: `stacks/foundation/network_stack.py`

```python
# 修改前: 允许整个 VPC CIDR
sg.add_ingress_rule(
    peer=ec2.Peer.ipv4(self.env_config.vpc.cidr),
    connection=ec2.Port.tcp(443),
)

# 修改后: 仅允许 Private 子网
for subnet in self.vpc.private_subnets + self.vpc.isolated_subnets:
    sg.add_ingress_rule(
        peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block),
        connection=ec2.Port.tcp(443),
        description=f"Allow HTTPS from {subnet.node.id}",
    )
```

### 1.4 DRY 重构 — IAM 角色创建统一

**问题**: EksStack 有内联的 `_create_irsa_role()` 方法，而 `utils/iam_helpers.py` 已有 `create_irsa_conditions()` 但缺少完整的 IRSA 角色创建函数

**修改文件**:

- `utils/iam_helpers.py` — 新增 `create_irsa_role()` 函数:
  ```python
  def create_irsa_role(
      scope: Construct,
      construct_id: str,
      env_config: EnvironmentConfig,
      eks_oidc_provider: eks.IOpenIdConnectProvider,
      role_name_suffix: str,
      service_account: str,
      namespace: str = "kube-system",
      description: str = "",
      managed_policies: list[str] | None = None,
  ) -> iam.Role:
      """创建 IRSA 角色 (统一替代 EksStack._create_irsa_role)."""
  ```

- `stacks/compute/eks_stack.py` — 移除内联 `_create_irsa_role()`, 改为调用 `utils.iam_helpers.create_irsa_role()`

### 1.5 测试补全

**新增测试文件**:

| 文件 | 测试目标 |
|------|---------|
| `tests/unit/test_iam_helpers.py` | `create_tagged_role`, `create_pod_identity_role`, `create_irsa_role`, `add_policy_statement` |
| `tests/unit/test_gpu_node_group.py` | GpuNodeGroupConstruct 各种配置组合 |

### 1.6 规范文档更新

- `stacks/__init__.py` 顶部 docstring — 更新分层说明，反映 `storage/` 目录
- `.claude/rules/architecture.md` — 更新目录职责表
- `infrastructure/cdk/CLAUDE.md` — 同步更新（如需要）

---

## Phase 2: 安全增强与监控能力

### 2.1 KMS Key 集中管理

**新文件**: `cdk_constructs/kms_key.py`

```python
@dataclass(frozen=True)
class KmsKeyConfig:
    alias_suffix: str
    description: str
    enable_key_rotation: bool = True

class PlatformKmsKey(Construct):
    """统一的 KMS Key Construct — 自动轮换 + 环境标签 + 标准别名命名."""
```

**创建 3 个 KMS Key**（在 IamStack 或新建的 SecurityFoundationStack 中）:
1. `ai-platform-{env}-s3-key` — S3 bucket 加密
2. `ai-platform-{env}-rds-key` — Aurora 加密
3. `ai-platform-{env}-ebs-key` — EBS 卷加密

**修改文件**:

| 文件 | 修改 |
|------|------|
| `stacks/storage/storage_stack.py` | S3 加密从 `S3_MANAGED` 改为 KMS + 自定义 key |
| `stacks/data/database_stack.py` | Aurora 使用自定义 `storage_encryption_key` |
| `cdk_constructs/gpu_node_group.py` | EBS 加密使用自定义 key |
| `app.py` | 传递 KMS key 到各 Stack 构造函数 |

### 2.2 Observability Stack

**问题**: `HyperPodAddonsStack` 中 `_observability_addon = None` 被注释掉

**新文件**: `stacks/observability/__init__.py`, `stacks/observability/observability_stack.py`

```python
class ObservabilityStack(cdk.Stack):
    """可观测性 Stack.

    创建:
    - Amazon Managed Prometheus (AMP) Workspace
    - HyperPod Observability EKS Add-on（连接到 AMP remote write）
    - IAM roles (Pod Identity) for Prometheus remote write
    """
```

**配置扩展** — `config/environments.py` 新增:

```python
@dataclass(frozen=True)
class ObservabilityConfig:
    enable_amp: bool = True
    amp_retention_days: int = 150
```

将此字段添加到 `EnvironmentConfig`，并在各环境工厂方法中设置。

**修改文件**:

| 文件 | 修改 |
|------|------|
| `config/environments.py` | 新增 `ObservabilityConfig`，添加到 `EnvironmentConfig` |
| `app.py` | 新增 ObservabilityStack 实例化，依赖 EksStack |
| `stacks/__init__.py` | 新增 ObservabilityStack 导出 |
| `stacks/compute/hyperpod_addons_stack.py` | 移除 `_observability_addon` 相关注释代码 |

**app.py 中新增**:

```python
# Layer 4.5: Observability
observability_stack = ObservabilityStack(
    app, f"{stack_prefix}-observability",
    env_config=env_config,
    eks_cluster=eks_stack.eks_cluster,
    env=env_config.to_cdk_environment(),
)
observability_stack.add_dependency(eks_stack)
observability_stack.add_dependency(hyperpod_addons_stack)
```

### 2.3 K8s RBAC Manifest

**新目录**: `infrastructure/k8s/rbac/`

| 文件 | 内容 |
|------|------|
| `cluster-roles.yaml` | 4 个 ClusterRole: `platform-admin`, `tenant-admin`, `training-user`, `viewer` |
| `training-job-role.yaml` | 训练任务执行 Role（允许创建 PyTorchJob、查看 Pod 日志） |

### 2.4 K8s Pod Security Admission

**新目录**: `infrastructure/k8s/security/`

| 文件 | 内容 |
|------|------|
| `namespace-psa-labels.yaml` | 为 `training-jobs`、`monitoring` 等 Namespace 添加 PSA enforce 标签 |

### 2.5 Snapshot 测试

**新文件**: `tests/unit/test_snapshot.py`

为每个 Stack 生成 CloudFormation 模板快照并进行 diff 比较，防止意外变更。

**新目录**: `tests/unit/snapshots/` — 存放 JSON 快照文件（首次运行自动生成）

### 2.6 测试补全

**新增测试文件**:

| 文件 | 测试目标 |
|------|---------|
| `tests/unit/test_kms_key.py` | PlatformKmsKey Construct |
| `tests/unit/test_observability_stack.py` | ObservabilityStack |

---

## Phase 3: K8s Kustomize 重构与功能补全

### 3.1 K8s Manifest Kustomize 重构

**目标结构**:

```
infrastructure/k8s/
├── base/                              # 基础配置
│   ├── kustomization.yaml             # 新建
│   ├── hyperpod-addons/               # 现有文件迁移
│   │   ├── training/
│   │   ├── ops/
│   │   └── spaces/
│   ├── network-policies/              # 现有文件迁移
│   ├── storage/                       # 现有文件迁移
│   ├── rbac/                          # Phase 2 新增
│   └── security/                      # Phase 2 新增
├── overlays/                          # 环境覆盖层
│   ├── dev/
│   │   ├── kustomization.yaml         # dev 补丁引用
│   │   └── patches/
│   │       ├── reduce-replicas.yaml   # 缩减副本数
│   │       └── reduce-quotas.yaml     # 缩减资源配额
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── prod/
│       ├── kustomization.yaml
│       └── patches/
│           ├── enable-ha.yaml         # 高可用配置
│           └── strict-policy.yaml     # 严格网络策略
└── scripts/
    ├── inject-cdk-outputs.sh          # 从 CDK CloudFormation 输出注入变量
    └── apply-manifests.sh             # 统一部署脚本
```

**迁移步骤**:
1. 创建 `base/` 目录，将现有 manifest 移入
2. 移除 manifest 中的 `${VARIABLE}` 占位符，使用 Kustomize `replacements` 机制
3. 创建 `overlays/{dev,staging,prod}/` 目录
4. 编写 `inject-cdk-outputs.sh` 从 CloudFormation Outputs 生成 `.env` 文件

### 3.2 Spot 实例支持

**修改文件**:

- `cdk_constructs/gpu_node_group.py` — `GpuNodeGroupConfig` 新增 `capacity_type: str = "ON_DEMAND"` 字段
- `infrastructure/k8s/base/hyperpod-addons/training/resource-flavors.yaml` — 新增 Spot flavor:
  ```yaml
  apiVersion: kueue.x-k8s.io/v1beta1
  kind: ResourceFlavor
  metadata:
    name: nvidia-a100-40gb-spot
  spec:
    nodeLabels:
      eks.amazonaws.com/capacityType: SPOT
    nodeTaints:
      - key: eks.amazonaws.com/spot
        value: "true"
        effect: NoSchedule
  ```

### 3.3 Application Stack（ECR）

**新文件**: `stacks/application/__init__.py`, `stacks/application/application_stack.py`

```python
class ApplicationStack(cdk.Stack):
    """后端应用部署 Stack.

    创建:
    - ECR Repository (后端 Docker 镜像仓库)
    - 服务发现配置
    """
```

**依赖**: EksStack, DatabaseStack, StorageStack

### 3.4 路径管理优化

**修改文件**: `config/constants.py` — 新增 `ProjectPaths` dataclass:

```python
@dataclass(frozen=True)
class ProjectPaths:
    CDK_ROOT: ClassVar[Path] = Path(__file__).parent.parent
    RESOURCES_DIR: ClassVar[Path] = CDK_ROOT / "resources"
    HELM_CHARTS_DIR: ClassVar[Path] = RESOURCES_DIR / "helm_charts"
```

**修改文件**: `stacks/compute/eks_stack.py` — 替换硬编码 `Path(__file__).parent.parent.parent / "resources"` 为 `ProjectPaths.HELM_CHARTS_DIR`

---

## 完整文件变更清单

### 新增文件

| 文件 | Phase | 用途 |
|------|-------|------|
| `stacks/storage/__init__.py` | P1 | Storage 层模块导出 |
| `tests/unit/test_iam_helpers.py` | P1 | IAM helpers 单元测试 |
| `tests/unit/test_gpu_node_group.py` | P1 | GPU NodeGroup 单元测试 |
| `cdk_constructs/kms_key.py` | P2 | 集中 KMS Key Construct |
| `stacks/observability/__init__.py` | P2 | Observability 层模块导出 |
| `stacks/observability/observability_stack.py` | P2 | AMP + Observability addon |
| `k8s/rbac/cluster-roles.yaml` | P2 | K8s ClusterRole 定义 |
| `k8s/rbac/training-job-role.yaml` | P2 | 训练任务执行 Role |
| `k8s/security/namespace-psa-labels.yaml` | P2 | Pod Security Admission |
| `tests/unit/test_snapshot.py` | P2 | Snapshot 测试 |
| `tests/unit/snapshots/` | P2 | Snapshot JSON 目录 |
| `tests/unit/test_kms_key.py` | P2 | KMS Construct 测试 |
| `tests/unit/test_observability_stack.py` | P2 | Observability Stack 测试 |
| `stacks/application/__init__.py` | P3 | Application 层模块导出 |
| `stacks/application/application_stack.py` | P3 | ECR + 应用部署 |
| `k8s/base/kustomization.yaml` | P3 | Kustomize base |
| `k8s/overlays/{dev,staging,prod}/kustomization.yaml` | P3 | 环境覆盖层 |
| `k8s/overlays/{dev,staging,prod}/patches/*.yaml` | P3 | 环境差异补丁 |
| `k8s/scripts/inject-cdk-outputs.sh` | P3 | CDK 输出注入脚本 |
| `k8s/scripts/apply-manifests.sh` | P3 | 统一部署脚本 |

### 修改文件

| 文件 | Phase | 修改内容 |
|------|-------|---------|
| `stacks/__init__.py` | P1 | 更新导入路径 (storage/), 更新 docstring |
| `stacks/data/__init__.py` | P1 | 移除 StorageStack, FsxLustreStack 导出 |
| `app.py` | P1+P2 | 启用 dev CDK Nag; 新增 ObservabilityStack |
| `utils/nag_suppressions.py` | P1 | 补充 dev 环境抑制规则（如需要） |
| `utils/iam_helpers.py` | P1 | 新增 `create_irsa_role()` |
| `stacks/compute/eks_stack.py` | P1+P3 | 移除内联 IRSA 方法; 替换硬编码路径 |
| `stacks/foundation/network_stack.py` | P1 | VPC Endpoint 安全组缩小到子网级别 |
| `.claude/rules/architecture.md` | P1 | 更新目录职责表和分层说明 |
| `config/environments.py` | P2 | 新增 ObservabilityConfig |
| `config/constants.py` | P3 | 新增 ProjectPaths |
| `stacks/storage/storage_stack.py` | P2 | 使用 KMS Key 替代 S3_MANAGED |
| `stacks/data/database_stack.py` | P2 | 使用自定义 KMS Key |
| `cdk_constructs/gpu_node_group.py` | P2+P3 | KMS Key for EBS; Spot capacity_type |
| `stacks/compute/hyperpod_addons_stack.py` | P2 | 移除 observability 注释代码 |
| `k8s/hyperpod-addons/training/resource-flavors.yaml` | P3 | 新增 Spot flavors |

---

## 验证方案

### Phase 1 验证

```bash
# 1. 确认导入路径正确
cd infrastructure/cdk
python -c "from stacks import StorageStack, FsxLustreStack, DatabaseStack; print('OK')"

# 2. 类型检查通过
mypy .

# 3. Lint 通过
ruff check . && ruff format --check .

# 4. 所有单元测试通过（含新增测试）
pytest -m unit -v

# 5. CDK Synth 成功（dev 环境，验证 Nag 全环境启用无报错）
cdk synth --context env=dev

# 6. CDK Diff 确认变更范围合理
cdk diff --context env=dev
```

### Phase 2 验证

```bash
# 1. 新增 Stack/Construct 的测试通过
pytest tests/unit/test_kms_key.py tests/unit/test_observability_stack.py tests/unit/test_snapshot.py -v

# 2. CDK Synth 包含新 Stack
cdk synth --context env=dev 2>&1 | grep -E "observability|kms"

# 3. 覆盖率检查
pytest -m unit --cov=stacks --cov=cdk_constructs --cov-report=term-missing
# 目标: stacks/ ≥90%, cdk_constructs/ ≥85%

# 4. K8s manifest 语法验证
kubectl apply --dry-run=client -f k8s/rbac/
kubectl apply --dry-run=client -f k8s/security/
```

### Phase 3 验证

```bash
# 1. Kustomize build 验证
kubectl kustomize k8s/overlays/dev/
kubectl kustomize k8s/overlays/staging/
kubectl kustomize k8s/overlays/prod/

# 2. CDK 输出注入脚本验证（需要已部署的 Stack）
bash k8s/scripts/inject-cdk-outputs.sh dev

# 3. 完整测试套件
make test-cov

# 4. 完整 CDK Synth（所有环境）
cdk synth --context env=dev
cdk synth --context env=staging
cdk synth --context env=prod
```

---

## 重构安全保障策略

本方案的核心原则是 **零功能回归** — 每一步重构都必须保证现有功能不受影响。以下是具体的保障机制：

### 保障机制 1: CDK Synth 等价性验证

**目标**: 确保目录重组和 DRY 重构后，生成的 CloudFormation 模板与重构前完全一致

**操作流程**:
```bash
# 步骤 1: 重构前 — 保存基准模板
cdk synth --context env=dev -o cdk.out.baseline

# 步骤 2: 执行重构
# ... (目录迁移、import 路径更新等)

# 步骤 3: 重构后 — 生成新模板
cdk synth --context env=dev -o cdk.out.refactored

# 步骤 4: 逐 Stack 对比模板差异
diff -r cdk.out.baseline/ cdk.out.refactored/
```

**预期结果**:
- Phase 1.1 目录重组 → **模板零差异**（纯文件移动 + import 路径调整）
- Phase 1.4 DRY 重构 → **模板零差异**（函数提取不改变资源定义）
- Phase 1.2 CDK Nag → **模板零差异**（Nag 是检查工具，不修改模板）
- Phase 1.3 安全组加固 → **模板有差异**（预期变更：安全组规则从 1 条变为多条子网规则）

只有 **安全组加固** 会产生模板差异，且差异范围可通过 `cdk diff` 精确预览。

### 保障机制 2: 分层验证门控

每个子任务完成后，必须通过以下验证门控才能进入下一步：

```
┌─────────────────────────────────────────────────────┐
│  验证门控 (每个子任务完成后必须全部通过)                │
│                                                     │
│  Gate 1: python -c "from stacks import *"  → OK     │
│  Gate 2: mypy .                            → 0 errors│
│  Gate 3: ruff check .                      → 0 errors│
│  Gate 4: pytest -m unit                    → ALL PASS │
│  Gate 5: cdk synth --context env=dev       → SUCCESS  │
│                                                     │
│  任一 Gate 失败 → 立即停止，回滚到上一步               │
└─────────────────────────────────────────────────────┘
```

### 保障机制 3: Git 分支策略

```
001-ai-training-platform-ddd-mm (当前工作分支)
  └── infra/phase1-restructure     ← Phase 1 重构分支
      ├── commit: "refactor: 创建 stacks/storage/ 目录"
      ├── commit: "refactor: 提取 create_irsa_role 到 iam_helpers"
      ├── commit: "fix: 启用 dev 环境 CDK Nag"
      └── commit: "fix: 缩小 VPC Endpoint 安全组范围"
  └── infra/phase2-security        ← Phase 2 安全分支
  └── infra/phase3-kustomize       ← Phase 3 功能分支
```

**规则**:
- 每个 Phase 使用独立分支
- 每个子任务单独 commit（方便精确回滚）
- 完成验证门控后才合并到工作分支
- `cdk synth` 基准模板保存在 commit 中作为对比基线

### 保障机制 4: 新增功能与重构解耦

将变更严格分为两类：

| 变更类型 | 特征 | 风险等级 | 验证方式 |
|---------|------|---------|---------|
| **纯重构** | 不改变 CloudFormation 输出 | 低 | CDK Synth diff = 0 |
| **新增功能** | 新增 Stack/资源/配置 | 中 | 新增测试 + CDK Synth 新增资源 |
| **行为修改** | 改变现有资源属性 | 高 | CDK Diff 精确预览 + 人工确认 |

- Phase 1.1 (目录重组) + 1.4 (DRY) = **纯重构** → 模板零差异
- Phase 1.2 (Nag) = **纯重构** → 模板零差异
- Phase 1.3 (安全组) = **行为修改** → CDK Diff 预览 + 确认
- Phase 2 (KMS/Observability) = **新增功能** → 新 Stack，不影响现有
- Phase 2 (KMS 替换 S3_MANAGED) = **行为修改** → CDK Diff 预览 + 确认
- Phase 3 (K8s Kustomize) = 不影响 CDK Stack → 独立验证

### 保障机制 5: 行为修改项的特殊处理

对于 **安全组加固** 和 **KMS 替换** 这两个会改变现有资源行为的变更：

**安全组加固**:
```bash
# 1. CDK Diff 预览变更
cdk diff --context env=dev 2>&1 | grep -A5 "SecurityGroup"

# 2. 验证新规则覆盖所有合法访问路径
# Private 子网 + Isolated 子网 = 所有需要访问 VPC Endpoint 的子网
# Public 子网不需要（通过 NAT → Internet 访问 AWS 服务）

# 3. 如果已有实际部署环境，先在 dev 部署验证无功能中断
```

**KMS 替换 S3_MANAGED** (Phase 2):
```bash
# 1. 这是 Phase 2 的操作，不会在 Phase 1 执行
# 2. 新的 KMS Key 加密不影响已有数据的读取（AWS 透明处理）
# 3. CDK Diff 预览：S3 Bucket 的 encryption 属性变更
# 4. 建议先在 dev 环境部署验证，确认无问题后再推广到 staging/prod
```

### 保障机制 6: Snapshot 测试（Phase 2 建立，永久保护）

Phase 2 建立 Snapshot 测试后，所有后续变更都有模板级别的回归保护：
- 每次 `pytest` 运行会比较当前模板与快照
- 模板意外变更 → 测试失败 → 阻止合并
- 有意变更 → 更新快照 → commit 中明确记录差异原因

---

## 实施顺序说明

每个 Phase 内部的任务之间也有依赖关系：

- **Phase 1**: 1.1 目录重组 → 1.4 DRY 重构 → 1.2 CDK Nag → 1.3 安全组 → 1.5 测试 → 1.6 文档
- **Phase 2**: 2.1 KMS → 2.2 Observability → 2.3 RBAC || 2.4 PSA → 2.5 Snapshot 测试 → 2.6 测试
- **Phase 3**: 3.1 Kustomize 重构 → 3.2 Spot || 3.3 Application Stack || 3.4 路径优化

建议使用 Claude Code Agent Team 并行执行各 Phase 内的独立任务（如 Phase 2 中 RBAC 和 PSA 可并行）。
