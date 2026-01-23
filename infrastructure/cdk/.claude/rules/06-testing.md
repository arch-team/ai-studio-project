---
paths:
  - "tests/**/*.py"
  - "conftest.py"
---

# CDK 测试规范

## 测试分层

| 层级 | 目录 | 职责 |
|------|------|------|
| 单元测试 | `tests/unit/` | 单个 Stack/Construct |
| 集成测试 | `tests/integration/` | Stack 间交互 |

## 测试命令

```bash
pytest                              # 全部测试
pytest -m unit                      # 单元测试
pytest -m integration               # 集成测试
pytest tests/unit/test_network_stack.py  # 特定文件
pytest --cov=stacks --cov-report=html    # 覆盖率
```

---

## conftest.py Fixtures

```python
import pytest
import aws_cdk as cdk
from aws_cdk import Environment
from aws_cdk.assertions import Template
from config import EnvironmentConfig

@pytest.fixture
def test_account() -> str:
    return "123456789012"

@pytest.fixture
def test_region() -> str:
    return "us-west-2"

@pytest.fixture
def cdk_env(test_account: str, test_region: str) -> Environment:
    return Environment(account=test_account, region=test_region)

@pytest.fixture
def dev_config(test_account: str, test_region: str) -> EnvironmentConfig:
    return EnvironmentConfig.for_dev(test_account, test_region)

@pytest.fixture
def staging_config(test_account: str, test_region: str) -> EnvironmentConfig:
    return EnvironmentConfig.for_staging(test_account, test_region)

@pytest.fixture
def prod_config(test_account: str, test_region: str) -> EnvironmentConfig:
    return EnvironmentConfig.for_prod(test_account, test_region)

@pytest.fixture
def cdk_app() -> cdk.App:
    return cdk.App()

def get_template(stack: cdk.Stack) -> Template:
    return Template.from_stack(stack)
```

---

## Stack 测试模板

```python
import pytest
from aws_cdk import App
from aws_cdk.assertions import Match, Template
from config import EnvironmentConfig
from stacks.foundation import NetworkStack

@pytest.mark.unit
class TestNetworkStack:
    @pytest.fixture
    def template(self, cdk_app: App, dev_config: EnvironmentConfig, cdk_env) -> Template:
        stack = NetworkStack(cdk_app, "TestNetwork", env_config=dev_config, env=cdk_env)
        return Template.from_stack(stack)

    def test_vpc_created(self, template: Template) -> None:
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_cidr(self, template: Template) -> None:
        template.has_resource_properties("AWS::EC2::VPC", {
            "CidrBlock": "10.0.0.0/16",
            "EnableDnsHostnames": True,
        })

    def test_nat_gateway_count(self, template: Template) -> None:
        template.resource_count_is("AWS::EC2::NatGateway", 1)

@pytest.mark.unit
class TestNetworkStackProd:
    @pytest.fixture
    def template(self, cdk_app: App, prod_config: EnvironmentConfig, cdk_env) -> Template:
        stack = NetworkStack(cdk_app, "TestNetwork", env_config=prod_config, env=cdk_env)
        return Template.from_stack(stack)

    def test_nat_gateway_count_prod(self, template: Template) -> None:
        template.resource_count_is("AWS::EC2::NatGateway", 2)
```

---

## Construct 测试模板

```python
@pytest.mark.unit
class TestGpuNodeGroupConstruct:
    @pytest.fixture
    def mock_cluster(self, cdk_app: App) -> eks.ICluster:
        """模拟 EKS 集群 (用于测试依赖 EKS 的 Construct)"""
        stack = Stack(cdk_app, "MockStack")
        return eks.Cluster.from_cluster_attributes(
            stack, "MockCluster",
            cluster_name="test-cluster",
            kubectl_role_arn="arn:aws:iam::123456789012:role/test",
        )

    @pytest.fixture
    def template(self, cdk_app: App, mock_cluster: eks.ICluster, dev_config) -> Template:
        stack = Stack(cdk_app, "TestStack")
        GpuNodeGroupConstruct(
            stack, "TestGpuNodeGroup",
            cluster=mock_cluster,
            props=GpuNodeGroupProps(instance_type=ec2.InstanceType("p4d.24xlarge")),
            env_config=dev_config,
        )
        return Template.from_stack(stack)

    def test_gpu_ami_type(self, template: Template) -> None:
        template.has_resource_properties("AWS::EKS::Nodegroup", {"AmiType": "AL2_x86_64_GPU"})

    def test_imdsv2_required(self, template: Template) -> None:
        template.has_resource_properties("AWS::EC2::LaunchTemplate", {
            "LaunchTemplateData": {"MetadataOptions": {"HttpTokens": "required"}}
        })
```

---

## 配置测试模板

```python
@pytest.mark.unit
class TestEnvironmentConfig:
    def test_dev_config_defaults(self) -> None:
        config = EnvironmentConfig.for_dev("123456789012", "us-west-2")
        assert config.environment_name == "dev"
        assert config.vpc.nat_gateways == 1
        assert config.protection.deletion_protection is False

    def test_prod_config_defaults(self) -> None:
        config = EnvironmentConfig.for_prod("123456789012", "us-west-2")
        assert config.environment_name == "prod"
        assert config.vpc.nat_gateways == 2
        assert config.protection.deletion_protection is True

    def test_config_immutability(self) -> None:
        """验证 dataclass(frozen=True) 配置不可变"""
        config = EnvironmentConfig.for_dev("123456789012", "us-west-2")
        with pytest.raises(AttributeError):
            config.environment_name = "modified"  # type: ignore
```

---

## 集成测试模板

```python
@pytest.mark.integration
class TestStackIntegration:
    @pytest.fixture
    def stacks(self, cdk_app: App, dev_config: EnvironmentConfig, cdk_env) -> dict:
        network = NetworkStack(cdk_app, "Network", env_config=dev_config, env=cdk_env)
        iam = IamStack(cdk_app, "Iam", env_config=dev_config, env=cdk_env)
        eks = EksStack(cdk_app, "Eks", env_config=dev_config, vpc=network.vpc,
                       node_role=iam.eks_node_role, env=cdk_env)
        eks.add_dependency(network)
        eks.add_dependency(iam)
        return {"network": network, "iam": iam, "eks": eks}

    def test_stack_dependencies(self, stacks: dict) -> None:
        assert stacks["network"] in stacks["eks"].dependencies
        assert stacks["iam"] in stacks["eks"].dependencies
```

---

## 常用断言

```python
# 资源数量
template.resource_count_is("AWS::EC2::VPC", 1)

# 资源属性
template.has_resource_properties("AWS::EC2::VPC", {"CidrBlock": "10.0.0.0/16"})

# 模糊匹配
template.has_resource_properties("AWS::EC2::Subnet", {
    "Tags": Match.array_with([Match.object_like({"Key": "Name"})])
})

# 正则匹配
template.has_resource_properties("AWS::EC2::VPCEndpoint", {
    "ServiceName": Match.string_like_regexp(".*s3.*")
})

# 任意值
Match.any_value()
Match.greater_than_or_equal(3)
```

---

## 测试原则

**必须测试**:
1. 资源创建 (resource_count_is)
2. 安全配置 (加密、IAM)
3. 环境差异 (dev/prod 不同配置)

**禁止**:
```python
# ❌ 整个模板断言 (脆弱)
assert template.to_json() == expected_json

# ❌ 跳过测试
@pytest.mark.skip(reason="TODO")

# ✅ 断言特定属性
template.has_resource_properties("AWS::EC2::VPC", {"CidrBlock": "10.0.0.0/16"})
```

## 覆盖率目标

- `config/`: 100%
- `stacks/`: ≥90%
- `cdk_constructs/`: ≥85%
