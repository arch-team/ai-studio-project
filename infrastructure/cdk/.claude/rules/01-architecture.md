# CDK 架构规范

## Stack 依赖规则

```
L1: NetworkStack, IamStack (并行)
L2: DatabaseStack, StorageStack (并行)
L3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
L4: FsxLustreStack
L5: AlbStack
```

**强制规则**:
1. 上层只依赖下层，禁止反向依赖
2. 通过构造函数参数传递资源 (依赖注入)
3. 禁止 `Fn.import_value()` 跨 Stack 引用

```python
# ✅ 正确
database_stack = DatabaseStack(app, "Database", vpc=network_stack.vpc)
database_stack.add_dependency(network_stack)

# ❌ 禁止
vpc_id = Fn.import_value("NetworkStack-VpcId")
```

## 目录职责

| 目录 | 职责 | 禁止 |
|------|------|------|
| `config/` | 纯配置数据类 | 创建 AWS 资源 |
| `stacks/` | Stack 实现 | 业务逻辑 |
| `cdk_constructs/` | 可复用 Construct | 依赖特定 Stack |
| `utils/` | 无状态工具函数 | 持有状态 |

## VPC 子网设计

| 层级 | CIDR | 用途 |
|------|------|------|
| Public | /20 | NAT, ALB |
| PrivateApp | /19 | EKS 节点 |
| PrivateData | /20 (isolated) | FSx, Aurora |

**必需 VPC Endpoints**: `s3`, `ecr.api`, `ecr.dkr`, `logs`, `sts`, `sagemaker.api`
