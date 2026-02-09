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
@pytest.fixture
def cdk_env() -> Environment:
    return Environment(account="123456789012", region="us-west-2")

@pytest.fixture
def dev_config() -> EnvironmentConfig:
    return EnvironmentConfig.for_dev("123456789012", "us-west-2")

@pytest.fixture
def cdk_app() -> cdk.App:
    return cdk.App()
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
