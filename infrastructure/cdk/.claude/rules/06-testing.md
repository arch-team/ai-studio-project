---
paths:
  - "tests/**/*.py"
  - "conftest.py"
---

# CDK 测试规范

## 测试分层

| 层级 | 目录 | 职责 | 速度 |
|------|------|------|------|
| 单元测试 | `tests/unit/` | 验证单个 Stack/Construct | 快 (<1s) |
| 集成测试 | `tests/integration/` | 验证 Stack 间交互 | 中 (<10s) |
| 快照测试 | `tests/snapshot/` | 检测意外变更 | 快 |

---

## 测试命令

```bash
# 运行所有测试
pytest

# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration

# 运行特定 Stack 测试
pytest tests/unit/test_network_stack.py

# 生成覆盖率报告
pytest --cov=stacks --cov=cdk_constructs --cov-report=html

# 更新快照
pytest --snapshot-update
```

---

## conftest.py Fixtures

### 标准 Fixtures

```python
"""测试 Fixtures"""
import pytest
import aws_cdk as cdk
from aws_cdk import Environment
from aws_cdk.assertions import Template

from config import EnvironmentConfig


# ========== 环境配置 Fixtures ==========

@pytest.fixture
def test_account() -> str:
    """测试 AWS 账户 ID"""
    return "123456789012"


@pytest.fixture
def test_region() -> str:
    """测试 AWS 区域"""
    return "us-west-2"


@pytest.fixture
def cdk_env(test_account: str, test_region: str) -> Environment:
    """CDK 环境"""
    return Environment(account=test_account, region=test_region)


@pytest.fixture
def dev_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """开发环境配置"""
    return EnvironmentConfig.for_dev(test_account, test_region)


@pytest.fixture
def staging_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """预发布环境配置"""
    return EnvironmentConfig.for_staging(test_account, test_region)


@pytest.fixture
def prod_config(test_account: str, test_region: str) -> EnvironmentConfig:
    """生产环境配置"""
    return EnvironmentConfig.for_prod(test_account, test_region)


# ========== CDK App Fixtures ==========

@pytest.fixture
def cdk_app() -> cdk.App:
    """测试用 CDK App"""
    return cdk.App()


# ========== 辅助函数 ==========

def get_template(stack: cdk.Stack) -> Template:
    """从 Stack 获取 CloudFormation 模板"""
    return Template.from_stack(stack)


def assert_resource_count(
    template: Template,
    resource_type: str,
    count: int,
) -> None:
    """断言资源数量"""
    template.resource_count_is(resource_type, count)


def assert_resource_properties(
    template: Template,
    resource_type: str,
    properties: dict,
) -> None:
    """断言资源属性"""
    template.has_resource_properties(resource_type, properties)
```

---

## 单元测试模板

### Stack 测试

```python
"""NetworkStack 单元测试"""
import pytest
from aws_cdk import App
from aws_cdk.assertions import Match, Template

from config import EnvironmentConfig
from stacks.foundation import NetworkStack


@pytest.mark.unit
class TestNetworkStack:
    """NetworkStack 测试套件"""

    @pytest.fixture
    def template(
        self,
        cdk_app: App,
        dev_config: EnvironmentConfig,
        cdk_env,
    ) -> Template:
        """创建测试 Template"""
        stack = NetworkStack(
            cdk_app,
            "TestNetwork",
            env_config=dev_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    # ========== VPC 测试 ==========

    def test_vpc_created(self, template: Template) -> None:
        """验证 VPC 创建"""
        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_cidr(self, template: Template) -> None:
        """验证 VPC CIDR"""
        template.has_resource_properties(
            "AWS::EC2::VPC",
            {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
            },
        )

    # ========== 子网测试 ==========

    def test_public_subnets_created(self, template: Template) -> None:
        """验证公共子网创建"""
        template.resource_count_is(
            "AWS::EC2::Subnet",
            Match.greater_than_or_equal(3),
        )

    def test_subnet_tags(self, template: Template) -> None:
        """验证子网标签"""
        template.has_resource_properties(
            "AWS::EC2::Subnet",
            {
                "Tags": Match.array_with([
                    Match.object_like({
                        "Key": "aws-cdk:subnet-type",
                        "Value": Match.any_value(),
                    }),
                ]),
            },
        )

    # ========== NAT Gateway 测试 ==========

    def test_nat_gateway_count(self, template: Template) -> None:
        """验证 NAT Gateway 数量 (dev=1)"""
        template.resource_count_is("AWS::EC2::NatGateway", 1)

    # ========== VPC Endpoints 测试 ==========

    def test_s3_endpoint_created(self, template: Template) -> None:
        """验证 S3 Gateway Endpoint"""
        template.has_resource_properties(
            "AWS::EC2::VPCEndpoint",
            {
                "ServiceName": Match.string_like_regexp(".*s3.*"),
                "VpcEndpointType": "Gateway",
            },
        )


@pytest.mark.unit
class TestNetworkStackProd:
    """生产环境特定测试"""

    @pytest.fixture
    def template(
        self,
        cdk_app: App,
        prod_config: EnvironmentConfig,
        cdk_env,
    ) -> Template:
        stack = NetworkStack(
            cdk_app,
            "TestNetwork",
            env_config=prod_config,
            env=cdk_env,
        )
        return Template.from_stack(stack)

    def test_nat_gateway_count_prod(self, template: Template) -> None:
        """验证生产环境 NAT Gateway 数量"""
        template.resource_count_is("AWS::EC2::NatGateway", 2)
```

### Construct 测试

```python
"""GpuNodeGroupConstruct 单元测试"""
import pytest
from aws_cdk import App, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk.assertions import Match, Template

from cdk_constructs import GpuNodeGroupConstruct, GpuNodeGroupProps
from config import EnvironmentConfig


@pytest.mark.unit
class TestGpuNodeGroupConstruct:
    """GPU 节点组 Construct 测试"""

    @pytest.fixture
    def mock_cluster(self, cdk_app: App) -> eks.ICluster:
        """模拟 EKS 集群"""
        stack = Stack(cdk_app, "MockStack")
        return eks.Cluster.from_cluster_attributes(
            stack,
            "MockCluster",
            cluster_name="test-cluster",
            kubectl_role_arn="arn:aws:iam::123456789012:role/test",
        )

    @pytest.fixture
    def template(
        self,
        cdk_app: App,
        mock_cluster: eks.ICluster,
        dev_config: EnvironmentConfig,
    ) -> Template:
        stack = Stack(cdk_app, "TestStack")

        GpuNodeGroupConstruct(
            stack,
            "TestGpuNodeGroup",
            cluster=mock_cluster,
            props=GpuNodeGroupProps(
                instance_type=ec2.InstanceType("p4d.24xlarge"),
                min_size=0,
                max_size=10,
            ),
            env_config=dev_config,
        )

        return Template.from_stack(stack)

    def test_node_group_created(self, template: Template) -> None:
        """验证节点组创建"""
        template.resource_count_is("AWS::EKS::Nodegroup", 1)

    def test_gpu_ami_type(self, template: Template) -> None:
        """验证 GPU AMI 类型"""
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {"AmiType": "AL2_x86_64_GPU"},
        )

    def test_launch_template_imdsv2(self, template: Template) -> None:
        """验证 IMDSv2 强制"""
        template.has_resource_properties(
            "AWS::EC2::LaunchTemplate",
            {
                "LaunchTemplateData": {
                    "MetadataOptions": {
                        "HttpTokens": "required",
                    },
                },
            },
        )

    def test_gpu_taint_applied(self, template: Template) -> None:
        """验证 GPU 污点"""
        template.has_resource_properties(
            "AWS::EKS::Nodegroup",
            {
                "Taints": Match.array_with([
                    {
                        "Key": "nvidia.com/gpu",
                        "Value": "true",
                        "Effect": "NO_SCHEDULE",
                    },
                ]),
            },
        )
```

---

## 配置测试

```python
"""环境配置测试"""
import pytest

from config import EnvironmentConfig, VpcConfig, DeploymentMode


@pytest.mark.unit
class TestEnvironmentConfig:
    """环境配置测试"""

    def test_dev_config_defaults(self) -> None:
        """验证开发环境默认值"""
        config = EnvironmentConfig.for_dev("123456789012", "us-west-2")

        assert config.environment_name == "dev"
        assert config.vpc.nat_gateways == 1
        assert config.vpc.deployment_mode == DeploymentMode.SINGLE_AZ
        assert config.database.min_acu == 0.5
        assert config.protection.deletion_protection is False

    def test_prod_config_defaults(self) -> None:
        """验证生产环境默认值"""
        config = EnvironmentConfig.for_prod("123456789012", "us-west-2")

        assert config.environment_name == "prod"
        assert config.vpc.nat_gateways == 2
        assert config.vpc.deployment_mode == DeploymentMode.MULTI_AZ
        assert config.database.multi_az is True
        assert config.protection.deletion_protection is True
        assert config.protection.waf_enabled is True

    def test_config_immutability(self) -> None:
        """验证配置不可变"""
        config = EnvironmentConfig.for_dev("123456789012", "us-west-2")

        with pytest.raises(AttributeError):
            config.environment_name = "modified"  # type: ignore


@pytest.mark.unit
class TestVpcConfig:
    """VPC 配置测试"""

    def test_default_values(self) -> None:
        """验证默认值"""
        config = VpcConfig()

        assert config.cidr == "10.0.0.0/16"
        assert config.max_azs == 3
        assert config.nat_gateways == 1

    def test_custom_values(self) -> None:
        """验证自定义值"""
        config = VpcConfig(
            cidr="172.16.0.0/16",
            max_azs=2,
            nat_gateways=2,
        )

        assert config.cidr == "172.16.0.0/16"
        assert config.max_azs == 2
```

---

## 集成测试

```python
"""Stack 集成测试"""
import pytest
from aws_cdk import App
from aws_cdk.assertions import Template

from config import EnvironmentConfig
from stacks.foundation import NetworkStack, IamStack
from stacks.compute import EksStack


@pytest.mark.integration
class TestStackIntegration:
    """Stack 间集成测试"""

    @pytest.fixture
    def stacks(
        self,
        cdk_app: App,
        dev_config: EnvironmentConfig,
        cdk_env,
    ) -> dict:
        """创建完整 Stack 链"""
        network = NetworkStack(
            cdk_app, "Network",
            env_config=dev_config,
            env=cdk_env,
        )

        iam = IamStack(
            cdk_app, "Iam",
            env_config=dev_config,
            env=cdk_env,
        )

        eks = EksStack(
            cdk_app, "Eks",
            env_config=dev_config,
            vpc=network.vpc,
            node_role=iam.eks_node_role,
            env=cdk_env,
        )
        eks.add_dependency(network)
        eks.add_dependency(iam)

        return {
            "network": network,
            "iam": iam,
            "eks": eks,
        }

    def test_eks_uses_network_vpc(self, stacks: dict) -> None:
        """验证 EKS 使用 Network VPC"""
        eks_template = Template.from_stack(stacks["eks"])
        network_template = Template.from_stack(stacks["network"])

        # EKS 应引用 Network Stack 的 VPC
        eks_template.has_resource_properties(
            "Custom::AWSCDK-EKS-Cluster",
            {
                "Config": {
                    "resourcesVpcConfig": {
                        "subnetIds": Match.any_value(),
                    },
                },
            },
        )

    def test_stack_dependencies(self, stacks: dict) -> None:
        """验证 Stack 依赖关系"""
        assert stacks["network"] in stacks["eks"].dependencies
        assert stacks["iam"] in stacks["eks"].dependencies
```

---

## 快照测试

```python
"""快照测试"""
import pytest
from aws_cdk import App
from aws_cdk.assertions import Template


@pytest.mark.unit
class TestNetworkStackSnapshot:
    """NetworkStack 快照测试"""

    def test_template_snapshot(
        self,
        cdk_app: App,
        dev_config: EnvironmentConfig,
        cdk_env,
        snapshot,
    ) -> None:
        """验证模板未意外变更"""
        stack = NetworkStack(
            cdk_app, "Network",
            env_config=dev_config,
            env=cdk_env,
        )

        template = Template.from_stack(stack)
        assert template.to_json() == snapshot
```

---

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| `config/` | 100% | 100% |
| `stacks/foundation/` | 95% | 98% |
| `stacks/data/` | 90% | 93% |
| `stacks/compute/` | 85% | 87% |
| `cdk_constructs/` | 90% | 85% |
| `utils/` | 90% | 88% |

### 覆盖率报告

```bash
# 生成 HTML 报告
pytest --cov=stacks --cov=cdk_constructs --cov-report=html

# 输出到终端
pytest --cov=stacks --cov-report=term-missing
```

---

## 测试最佳实践

### 必须测试

1. **资源创建**: 验证关键资源存在
2. **资源属性**: 验证安全相关配置
3. **环境差异**: 验证 dev/staging/prod 配置差异
4. **边界条件**: 验证最小/最大值处理

### 禁止行为

```python
# ❌ 禁止: 直接断言整个模板
def test_template(template):
    assert template.to_json() == expected_json  # 过于脆弱

# ✅ 应该: 断言特定属性
def test_vpc_cidr(template):
    template.has_resource_properties("AWS::EC2::VPC", {"CidrBlock": "10.0.0.0/16"})
```

```python
# ❌ 禁止: 跳过测试
@pytest.mark.skip(reason="TODO: fix later")
def test_something():
    ...

# ✅ 应该: 修复或删除测试
```
