---
paths:
  - "tests/**/*.py"
  - "conftest.py"
---

# 测试规范

## 命令

```bash
pytest -m unit                  # 单元测试
pytest -m integration           # 集成测试
pytest --cov=stacks             # 覆盖率
```

## 核心 Fixtures (conftest.py)

```python
# 环境配置
@pytest.fixture
def dev_config() -> EnvironmentConfig:
    return EnvironmentConfig.for_dev("123456789012", "us-east-1")

@pytest.fixture
def cdk_app() -> cdk.App:
    return cdk.App()

@pytest.fixture
def cdk_env() -> Environment:
    return Environment(account="123456789012", region="us-east-1")
```

### 共用 Stack 依赖链 Fixtures

需要 EKS 依赖的 Stack (如 HyperPodAddonsStack, ObservabilityStack) 可复用:

```python
@pytest.fixture
def network_stack(cdk_app, dev_config, cdk_env) -> NetworkStack:
    return NetworkStack(cdk_app, "Network", env_config=dev_config, env=cdk_env)

@pytest.fixture
def eks_stack(cdk_app, dev_config, cdk_env, network_stack, iam_stack) -> EksStack:
    stack = EksStack(cdk_app, "Eks", env_config=dev_config,
                     vpc=network_stack.vpc, eks_node_role=iam_stack.eks_node_role, env=cdk_env)
    return stack
```

### 轻量级 Fixtures

不需要完整 Stack 依赖链时，使用轻量级 fixture:

```python
@pytest.fixture
def lightweight_eks_cluster(cdk_app, dev_config, cdk_env) -> eks.Cluster:
    """不经过 EksStack，直接创建简化的 EKS 集群。"""
    # 详见 tests/conftest.py
```

## Stack 测试模板

```python
@pytest.mark.unit
class TestNetworkStack:
    @pytest.fixture
    def template(self, cdk_app, dev_config, cdk_env) -> Template:
        stack = NetworkStack(cdk_app, "Test", env_config=dev_config, env=cdk_env)
        return Template.from_stack(stack)

    def test_vpc_created(self, template):
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_cidr(self, template):
        template.has_resource_properties("AWS::EC2::VPC", {"CidrBlock": "10.0.0.0/16"})
```

## Snapshot 测试

> 适用于验证 Stack 输出的 CloudFormation 模板没有意外变更。

```python
def test_network_stack_snapshot(self, template, snapshot):
    assert template.to_json() == snapshot
```

**注意**: Snapshot 仅用于回归检测，不替代细粒度断言。首次运行用 `--snapshot-update` 生成基准。

## 常用断言

```python
template.resource_count_is("AWS::EC2::VPC", 1)
template.has_resource_properties("AWS::EC2::VPC", {"CidrBlock": "..."})
template.has_resource_properties("AWS::EC2::Subnet", {
    "Tags": Match.array_with([Match.object_like({"Key": "Name"})])
})
```

## 覆盖率目标

| 目录 | 目标 |
|------|------|
| `config/` | 100% |
| `stacks/` | ≥90% |
| `cdk_constructs/` | ≥85% |

## 禁止

- ❌ `template.to_json() == expected` (脆弱)
- ❌ `@pytest.mark.skip`
