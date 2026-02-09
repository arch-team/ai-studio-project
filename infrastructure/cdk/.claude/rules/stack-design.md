---
paths:
  - "stacks/**/*.py"
  - "app.py"
---

# Stack 设计规范

## 结构模板

```python
class ExampleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 env_config: EnvironmentConfig, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self._env_config = env_config
        self._create_resources(vpc)
        apply_standard_tags(self, env_config)

    def _create_resources(self, vpc: ec2.IVpc) -> None:
        self._sg = ec2.SecurityGroup(self, "SG", vpc=vpc)

    @property
    def security_group(self) -> ec2.ISecurityGroup:
        return self._sg
```

## 方法命名

| 前缀 | 用途 |
|------|------|
| `_create_*` | 创建资源 |
| `_configure_*` | 配置资源 |
| `_setup_*` | 设置关联 |

## 依赖注入

必须注入: VPC, IAM 角色, KMS Key, Security Group

```python
def __init__(self, ..., vpc: ec2.IVpc, kms_key: kms.IKey | None = None):
    self._kms_key = kms_key or kms.Key(self, "Key", enable_key_rotation=True)
```

## 删除策略

> 完整的 RemovalPolicy 策略矩阵见 [deployment.md §1](deployment.md)（单一真实源）

## 条件创建

```python
def _create_waf(self) -> None:
    if not self._env_config.protection.waf_enabled:
        return
    self._waf = wafv2.CfnWebACL(self, "WebAcl", ...)
```
