# CDK 架构规范

## 分层架构

本项目采用严格的分层架构，每层有明确的职责边界。

### Stack 分层依赖图

```
Layer 1: Foundation (并行部署)
  ├─ NetworkStack      - VPC, 子网, VPC Endpoints
  └─ IamStack         - IAM 角色, 策略, 信任关系
        ↓
Layer 2: Data (并行部署)
  ├─ DatabaseStack    - Aurora Serverless v2
  └─ StorageStack     - S3 Buckets, KMS Keys
        ↓
Layer 3a: Compute Foundation
  └─ EksStack         - EKS 集群, Add-ons, Helm Charts
        ↓
Layer 3b: HyperPod
  └─ SagemakerHyperPodStack - SageMaker HyperPod 集群
        ↓
Layer 3c: HyperPod Add-ons
  └─ HyperPodAddonsStack - Training Operator, Kueue, Observability
        ↓
Layer 4: High-Performance Storage
  └─ FsxLustreStack   - FSx for Lustre, S3 Data Repository
        ↓
Layer 5: Ingress
  └─ AlbStack         - ALB, TLS, WAF
```

### 强制规则

1. **单向依赖**: 上层只能依赖下层，禁止反向依赖
2. **显式声明**: 所有跨 Stack 依赖必须在 `app.py` 中显式声明
3. **接口隔离**: 通过构造函数参数传递资源，不使用全局查找

### 依赖声明示例

```python
# ✅ 正确: 显式依赖声明
database_stack = DatabaseStack(app, "Database", vpc=network_stack.vpc)
database_stack.add_dependency(network_stack)

# ❌ 错误: 隐式依赖 (通过 Fn.import_value)
database_stack = DatabaseStack(app, "Database")
# 内部使用 Fn.import_value("VpcId")  # 禁止
```

---

## 目录结构规范

```
cdk/
├── app.py                      # CDK 入口 (唯一)
├── config/                     # 配置管理 (纯数据, 无业务逻辑)
│   ├── constants.py           # 常量定义
│   └── environments.py        # 环境配置
├── stacks/                     # Stack 实现 (按部署层级组织)
│   ├── foundation/            # Layer 1
│   ├── data/                  # Layer 2
│   ├── compute/               # Layer 3
│   └── networking/            # Layer 5
├── cdk_constructs/             # 可复用 Construct (L2/L3)
├── aspects/                    # CDK Aspects (全局行为)
├── utils/                      # 工具函数 (无状态)
├── resources/                  # 静态资源
│   ├── helm_charts/
│   └── scripts/
└── tests/                      # 测试代码
    ├── conftest.py
    ├── unit/
    └── integration/
```

### 目录职责

| 目录 | 职责 | 禁止行为 |
|------|------|----------|
| `config/` | 纯配置数据类 | 不创建 AWS 资源 |
| `stacks/` | Stack 实现 | 不包含业务逻辑 |
| `cdk_constructs/` | 可复用 Construct | 不依赖特定 Stack |
| `utils/` | 无状态工具函数 | 不持有状态 |
| `aspects/` | 全局行为修改 | 不创建新资源 |

---

## VPC 设计规范

### 3 层子网架构

| 层级 | CIDR | 用途 | 隔离级别 |
|------|------|------|----------|
| Public | /20 (4,096 IPs) | NAT Gateway, ALB | 公网可达 |
| PrivateApp | /19 (8,192 IPs) | EKS 节点, 计算资源 | NAT 出站 |
| PrivateData | /20 (4,096 IPs) | FSx, Aurora | 完全隔离 |

### VPC Endpoints

必须配置的 Endpoints (避免流量出 VPC):
- `s3` (Gateway)
- `ecr.api`, `ecr.dkr` (Interface)
- `logs`, `monitoring` (Interface)
- `sts` (Interface)
- `sagemaker.api`, `sagemaker.runtime` (Interface)

---

## Stack 命名规范

### 命名格式

```
{project}-{environment}-{component}
```

示例:
- `ai-platform-dev-network`
- `ai-platform-staging-eks`
- `ai-platform-prod-database`

### Construct ID 规范

- 使用 PascalCase
- 描述性命名，体现资源用途
- 避免缩写 (除非广泛认知)

```python
# ✅ 正确
self.vpc = ec2.Vpc(self, "MainVpc", ...)
self.training_bucket = s3.Bucket(self, "TrainingDataBucket", ...)

# ❌ 错误
self.vpc = ec2.Vpc(self, "vpc1", ...)
self.bucket = s3.Bucket(self, "Bkt", ...)
```

---

## 资源导出规范

### 跨 Stack 资源共享

通过属性暴露，不使用 `CfnOutput` + `Fn.import_value`:

```python
class NetworkStack(Stack):
    def __init__(self, ...):
        self._vpc = ec2.Vpc(...)

    @property
    def vpc(self) -> ec2.IVpc:
        """暴露 VPC 供其他 Stack 使用"""
        return self._vpc

# 使用方
eks_stack = EksStack(app, "EKS", vpc=network_stack.vpc)
```

### CfnOutput 使用场景

仅用于:
1. 外部系统需要的值 (如 ALB DNS)
2. 运维脚本需要查询的值
3. 调试目的 (开发环境)

```python
CfnOutput(self, "AlbDnsName",
    value=self.alb.load_balancer_dns_name,
    description="ALB DNS name for external access",
    export_name=f"{self.stack_name}-alb-dns"
)
```
