# Infrastructure 审查问题修复计划

## Context

4 个专家 Agent 对 infrastructure 子项目完成了多维度深度审查，发现 62 个问题（2 CRITICAL / 7 HIGH / 9 MEDIUM）。本计划按优先级分批修复，使用任务清单跟踪进度。每批修复完成后运行完整验证门控。

修复原则：**最小改动、精确修复、逐项验证**。不做架构重构，只修复审查发现的具体问题。

---

## 批次一：P0 安全修复（CRITICAL + 高优先级安全）

### Task 1: 修复 IRSA 空条件 Confused Deputy [F-IAM-01] — CRITICAL

**文件**: `stacks/foundation/iam_stack.py`

**修复 1a — TrainingExecutionRole (第 186 行)**:
将 `conditions={}` 替换为 OIDC 条件约束：
```python
conditions={
    "StringEquals": {
        f"oidc.eks.{self.env_config.region}.amazonaws.com:sub":
            "system:serviceaccount:training-jobs:training-execution-sa",
        f"oidc.eks.{self.env_config.region}.amazonaws.com:aud":
            "sts.amazonaws.com",
    }
},
```

**修复 1b — BackendServiceRole (第 287 行)**:
同样替换 `conditions={}`：
```python
conditions={
    "StringEquals": {
        f"oidc.eks.{self.env_config.region}.amazonaws.com:sub":
            "system:serviceaccount:backend:backend-service-sa",
        f"oidc.eks.{self.env_config.region}.amazonaws.com:aud":
            "sts.amazonaws.com",
    }
},
```

**注意**: ServiceAccount 名称和 Namespace 需要与实际的后端部署配置一致。如果尚未确定，使用合理的默认值并添加注释说明。

---

### Task 2: 替换 FSx CSI AmazonFSxFullAccess [F-IAM-02] — CRITICAL

**文件**: `stacks/compute/eks_stack.py` (第 264 行)

将 `managed_policies=["AmazonFSxFullAccess"]` 替换为自定义最小权限策略：

```python
# 移除: managed_policies=["AmazonFSxFullAccess"],
# 改为创建角色后手动添加精确权限:
fsx_csi_role = create_irsa_role(
    ...
    managed_policies=[],  # 不使用托管策略
)
# FSx CSI Driver 仅需描述和挂载权限
from utils.iam_helpers import add_policy_statement
add_policy_statement(
    fsx_csi_role,
    sid="FsxCsiDescribe",
    actions=["fsx:DescribeFileSystems", "fsx:DescribeVolumes", "fsx:DescribeDataRepositoryAssociations"],
    resources=["*"],  # fsx:Describe 操作不支持资源级限制
)
```

---

### Task 3: 限制 EKS Admin 角色 assume 范围 [F-IAM-03] — HIGH

**文件**: `stacks/compute/eks_stack.py` (第 117 行)

将 `assumed_by=iam.AccountRootPrincipal()` 改为通过 CDK Context 或环境变量限定管理员角色：

```python
# 修改前:
assumed_by=iam.AccountRootPrincipal(),
# 修改后: 仅允许当前 CDK 部署角色 assume
assumed_by=iam.AccountRootPrincipal(),  # 保留，但添加 Condition
```

由于 CDK bootstrap 角色是动态的，更安全的做法是保留 `AccountRootPrincipal` 但添加 `conditions`：
```python
assumed_by=iam.AccountRootPrincipal().with_conditions({
    "StringEquals": {
        "aws:PrincipalTag/Role": "EKSAdmin",
    }
}),
```

**备选方案**: 如果上述条件过于复杂，至少在角色上添加 PermissionsBoundary 限制 assume 后的权限。

---

### Task 4: 限制 KMS 策略资源范围 [F-IAM-04] — HIGH

**文件**: `stacks/foundation/iam_stack.py` (第 393 行)

需要将 `resources=["*"]` 替换为实际的 KMS Key ARN。由于 KMS Key 在 `app.py` 中创建并传入，IamStack 需要接收 KMS Key ARN 参数：

```python
# 修改 IamStack 构造函数，增加 kms_key_arns 参数
# 将 resources=["*"] 改为:
resources=self._kms_key_arns,  # 仅允许访问平台自有 KMS Key
```

**修改文件**: `app.py` — 将 KMS Key ARN 传给 IamStack 或将 KMS 策略移到使用 Key 的 Stack 中。

---

### Task 5: 修复 S3 CORS 通配符 [F-NET-01] — HIGH

**文件**: `stacks/storage/storage_stack.py` (第 194 行)

```python
# 修改前:
allowed_origins=["*"],
# 修改后: 根据环境配置
allowed_origins=(
    ["*"] if self.env_config.name == EnvironmentType.DEV
    else [f"https://{self.env_config.resource_prefix}.example.com"]
),
```

需要从 `config/environments.py` 导入 `EnvironmentType`。

---

### Task 6: 移除 S3 加密降级回退 [F-DATA-01] — HIGH

**文件**: `stacks/storage/storage_stack.py` (第 106-112 行)

```python
# 修改前: 允许回退到 S3_MANAGED
if self._encryption_key:
    encryption = s3.BucketEncryption.KMS
    encryption_key_ref = self._encryption_key
else:
    encryption = s3.BucketEncryption.S3_MANAGED
    encryption_key_ref = None

# 修改后: 强制要求 KMS Key
if not self._encryption_key:
    raise ValueError("encryption_key is required — S3_MANAGED encryption is not allowed for this platform")
encryption = s3.BucketEncryption.KMS
encryption_key_ref = self._encryption_key
```

---

## 批次二：P1 成本优化

### Task 7: Dev FSx 缩减到 1.2 TiB [P1-1]

**文件**: `config/environments.py` (第 336 行)

```python
# 修改前:
fsx_storage_gib=10 * 1024,  # 10 TiB 最小值
# 修改后:
fsx_storage_gib=1200,  # 1.2 TiB (FSx 最小值，dev 够用)
```

---

### Task 8: Prod FSx 初始 20 TiB [P1-2]

**文件**: `config/environments.py` (第 376 行)

```python
# 修改前:
fsx_storage_gib=100 * 1024,  # 100 TiB
# 修改后:
fsx_storage_gib=20 * 1024,  # 20 TiB (初始容量，支持在线扩容)
```

---

### Task 9: Dev Aurora 移除 Reader [P1-4]

**文件**: `stacks/data/database_stack.py` (第 219-226 行)

将 Reader 创建改为条件化：
```python
# 修改前: 无条件创建
readers=[
    rds.ClusterInstance.serverless_v2("Reader", ...),
],

# 修改后: Dev 不创建 Reader
readers=(
    [rds.ClusterInstance.serverless_v2(
        "Reader",
        instance_identifier=f"{self.env_config.resource_prefix}-aurora-reader",
        scale_with_writer=True,
    )]
    if self.env_config.name != EnvironmentType.DEV
    else []
),
```

需要导入 `EnvironmentType`。

---

### Task 10: 移除不可行的 Spot ResourceFlavor [P1-7]

**文件**: `infrastructure/k8s/hyperpod-addons/training/resource-flavors.yaml` (第 77-108 行)

删除 `nvidia-a100-40gb-spot` ResourceFlavor 定义（HyperPod 不支持 Spot GPU）。添加注释说明原因：
```yaml
# 注意: HyperPod EKS 模式不支持 Spot GPU 实例。
# 如需降低 GPU 成本，应使用 Savings Plans 或 Reserved Instances。
```

---

### Task 11: HyperPod Add-on 版本锁定 [P1-6]

**文件**: `stacks/compute/hyperpod_addons_stack.py` (第 126-133 行)

在 `config/environments.py` 的 `EksConfig` 中新增 HyperPod Add-on 版本配置，并在 `_create_addon` 中使用：

```python
# hyperpod_addons_stack.py 修改 _create_addon:
addon = eks.CfnAddon(
    self,
    construct_id,
    addon_name=addon_name,
    addon_version=addon_version,  # 新增参数
    cluster_name=self._eks_cluster.cluster_name,
    ...
)
```

具体版本号需查询 AWS 文档 (`aws eks describe-addon-versions --addon-name <name>`)。

---

## 批次三：P1 安全加固

### Task 12: 收窄 CDK Nag Stack 级抑制 [F-NAG-01]

**文件**: `utils/nag_suppressions.py` (第 29-37 行)

将 `AwsSolutions-IAM5` 的 Stack 级抑制改为资源级抑制。需要在各 Stack 中使用 `NagSuppressions.add_resource_suppressions()` 针对**已知合理**的通配符权限单独抑制，而非全局抑制。

这是一个较大的改动，需要：
1. 从全局 suppressions 中移除 `AwsSolutions-IAM5`
2. 在每个需要通配符权限的资源上添加局部抑制
3. 运行 `cdk synth --context env=dev` 确认 Nag 不报新的 IAM5 错误

---

### Task 13: FSx + Aurora 安全组收窄 [P1-3, P1-5]

**文件**: `stacks/storage/fsx_stack.py` (第 185-195 行)
**文件**: `stacks/data/database_stack.py` (第 101-106 行)

将两处 VPC CIDR 规则改为仅允许 PrivateApp 子网：

```python
# FSx: 改为仅允许 Private 子网
for subnet in vpc.private_subnets:
    sg.add_ingress_rule(
        peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block),
        connection=ec2.Port.tcp(988),
        description=f"Lustre from {subnet.node.id}",
    )

# Aurora: 同样改为 Private 子网
for subnet in vpc.private_subnets:
    sg.add_ingress_rule(
        peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block),
        connection=ec2.Port.tcp(3306),
        description=f"MySQL from {subnet.node.id}",
    )
```

---

## 批次四：P2 测试质量

### Task 14: 重写 Snapshot 测试 [P2-1]

**文件**: `tests/unit/test_snapshot.py` (第 33-53 行)

将 `_normalize_template()` 改为保留完整资源属性（仅去除 CDK 生成的 hash）：

```python
def _normalize_template(template: Template) -> dict:
    raw = template.to_json()
    # 保留完整结构，仅移除动态 hash
    import re
    normalized = json.dumps(raw, sort_keys=True)
    normalized = re.sub(r'[a-f0-9]{64}', '<HASH>', normalized)
    normalized = re.sub(r'[A-F0-9]{8,}', '<TOKEN>', normalized)
    return json.loads(normalized)
```

运行 `pytest tests/unit/test_snapshot.py --snapshot-update` 重新生成快照。

---

### Task 15: 加强 EKS Stack 断言 [P2-2]

**文件**: `tests/unit/test_eks_stack.py`

将 `assert len(xxx) >= 1` 替换为 `has_resource_properties` 精确断言：

```python
def test_eks_cluster_configuration(self, template: Template) -> None:
    template.has_resource_properties("Custom::AWSCDK-EKS-Cluster", {
        "Config": {
            "version": "1.33",
            "resourcesVpcConfig": {
                "endpointPrivateAccess": True,
                "endpointPublicAccess": False,
            },
        },
    })
```

---

### Task 16: 新增 CDK Nag 合规测试 [P2-3]

**新文件**: `tests/unit/test_cdk_nag_compliance.py`

```python
"""CDK Nag 安全合规测试 — 验证所有 Stack 通过 AwsSolutionsChecks."""
from cdk_nag import AwsSolutionsChecks, NagPackSuppression
import aws_cdk as cdk

class TestCdkNagCompliance:
    def test_no_unsuppressed_errors(self, ...):
        """验证 Nag 检查无未抑制的错误."""
        # synth with Nag aspect, then check annotations
```

---

## 关键文件清单

| 文件 | 涉及 Task |
|------|----------|
| `stacks/foundation/iam_stack.py` | T1, T4 |
| `stacks/compute/eks_stack.py` | T2, T3 |
| `stacks/storage/storage_stack.py` | T5, T6 |
| `stacks/data/database_stack.py` | T9, T13 |
| `stacks/storage/fsx_stack.py` | T13 |
| `stacks/compute/hyperpod_addons_stack.py` | T11 |
| `config/environments.py` | T7, T8, T11 |
| `utils/nag_suppressions.py` | T12 |
| `app.py` | T4 |
| `k8s/hyperpod-addons/training/resource-flavors.yaml` | T10 |
| `tests/unit/test_snapshot.py` | T14 |
| `tests/unit/test_eks_stack.py` | T15 |
| `tests/unit/test_cdk_nag_compliance.py` | T16 (新建) |

---

## 验证方案

### 每批次验证门控

```bash
# Gate 1: 导入检查
python -c "from stacks import *; print('OK')"

# Gate 2: Lint
ruff check --exclude 'cdk.out*' .

# Gate 3: 测试
pytest tests/ --tb=short

# Gate 4: CDK Synth
cdk synth --context env=dev

# Gate 5: CDK Diff（确认变更范围合理）
cdk diff --context env=dev
```

### 批次一额外验证

```bash
# 验证 IAM 条件约束生效
cdk synth --context env=dev -o cdk.out.fix
python -c "
import json
tpl = json.load(open('cdk.out.fix/ai-platform-dev-iam.template.json'))
for k, v in tpl['Resources'].items():
    if v['Type'] == 'AWS::IAM::Role':
        policy = v.get('Properties', {}).get('AssumeRolePolicyDocument', {})
        for stmt in policy.get('Statement', []):
            cond = stmt.get('Condition', {})
            if 'sts:AssumeRoleWithWebIdentity' in str(stmt):
                assert cond, f'IRSA role {k} 缺少条件约束!'
                print(f'{k}: conditions OK')
"
```

### 批次二额外验证

```bash
# 验证 FSx 配置
python -c "
from config.environments import get_environment_config
dev = get_environment_config('dev')
assert dev.storage.fsx_storage_capacity_gib == 1200, f'Dev FSx 应为 1200, 实际 {dev.storage.fsx_storage_capacity_gib}'
prod = get_environment_config('prod')
assert prod.storage.fsx_storage_capacity_gib == 20 * 1024, f'Prod FSx 应为 20480'
print('FSx 配置验证通过')
"
```

---

## 执行方式

使用 Claude Code Agent Team 并行执行同批次内的独立任务：

- **批次一** (T1-T6): T1+T2 并行 → T3+T4+T5+T6 并行
- **批次二** (T7-T11): 全部并行（独立修改不同文件）
- **批次三** (T12-T13): 串行（T12 可能影响 synth 结果，需先完成再做 T13）
- **批次四** (T14-T16): 全部并行

每批次完成后运行验证门控，全部通过后进入下一批次。
