---
paths:
  - "cdk_constructs/**/*.py"
  - "aspects/**/*.py"
---

# Construct 设计规范

## 何时创建 L3 Construct

1. 同一资源组合出现 2+ 次
2. 配置项 > 5 个且有内在关联
3. 需要封装最佳实践

## 模板结构

```python
@dataclass(frozen=True)
class GpuNodeGroupProps:
    instance_type: ec2.InstanceType
    min_size: int = 0
    max_size: int = 10

class GpuNodeGroupConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *,
                 cluster: eks.ICluster, props: GpuNodeGroupProps) -> None:
        super().__init__(scope, construct_id)
        self._node_group = self._create_node_group(cluster, props)

    def _create_node_group(self, cluster, props) -> eks.Nodegroup:
        return eks.Nodegroup(self, "NodeGroup", cluster=cluster,
            instance_types=[props.instance_type],
            ami_type=eks.NodegroupAmiType.AL2_X86_64_GPU,
            taints=[eks.TaintSpec(key="nvidia.com/gpu", value="true",
                                  effect=eks.TaintEffect.NO_SCHEDULE)])

    @property
    def node_group(self) -> eks.Nodegroup:
        return self._node_group
```

## Props 设计

| 场景 | 使用 |
|------|------|
| 配置项 ≥ 5 | Props dataclass |
| 配置项 < 5 | 构造函数参数 |
| 依赖注入 | 构造函数参数 |

**规则**: `@dataclass(frozen=True)` + `__post_init__` 验证

## Aspect 模式

```python
class StandardTaggingAspect(IAspect):
    def __init__(self, env_config: EnvironmentConfig) -> None:
        self._env_config = env_config

    def visit(self, node: IConstruct) -> None:
        Tags.of(node).add("Environment", self._env_config.environment_name)

# app.py
cdk.Aspects.of(app).add(StandardTaggingAspect(env_config))
```

## 设计原则

- ✅ 组合优于继承
- ❌ 避免深度继承链
