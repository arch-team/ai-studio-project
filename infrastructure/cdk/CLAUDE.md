# CLAUDE.md

CDK 项目开发指南 - AI Training Platform 基础设施

> **回复语言**: 中文 (参见根目录 `CLAUDE.md`)

---

## 核心规则 (必须遵守)

### Stack 分层

```
Layer 1: NetworkStack, IamStack (并行)
Layer 2: DatabaseStack, StorageStack (并行)
Layer 3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
Layer 4: FsxLustreStack
Layer 5: AlbStack
```

**强制规则**:
- ✅ 上层只依赖下层，禁止反向依赖
- ✅ 通过构造函数参数传递资源 (依赖注入)
- ❌ 禁止使用 `Fn.import_value()` 跨 Stack 引用

### 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| Stack ID | PascalCase | `NetworkStack` |
| Construct ID | PascalCase | `MainVpc`, `TrainingBucket` |
| 资源名称 | kebab-case | `ai-platform-dev-vpc` |
| 私有方法 | _snake_case | `_create_vpc()` |
| 常量 | UPPER_SNAKE | `MAX_NODES` |

### 安全底线

1. **IAM**: 最小权限，禁止 `Action: "*"` 或 `Resource: "*"`
2. **加密**: 所有存储启用 KMS 加密，S3 强制 SSL
3. **网络**: 数据层使用 `PRIVATE_ISOLATED` 子网
4. **EC2**: 强制 IMDSv2 (`require_imdsv2=True`)
5. **CDK Nag**: staging/prod 必须通过安全检查

### 环境配置

| 配置 | Dev | Staging | Prod |
|------|-----|---------|------|
| NAT | 1 | 2 | 2 |
| 多 AZ | ❌ | ✅ | ✅ |
| WAF | ❌ | ❌ | ✅ |
| 删除保护 | ❌ | ✅ | ✅ |
| CDK Nag | 跳过 | 启用 | 启用 |

---

## 常用命令

```bash
# 代码质量
ruff check . && ruff format .   # Lint + Format
mypy .                          # 类型检查
pytest -m unit                  # 单元测试

# CDK 操作
cdk synth                       # 合成模板
cdk diff --context env=dev      # 查看变更
cdk deploy --context env=dev    # 部署
```

---

## 目录结构

```
cdk/
├── app.py                 # CDK 入口
├── config/
│   ├── constants.py       # 常量 (EKS_ADDON_NAMES, K8S_NAMESPACES)
│   └── environments.py    # 环境配置 (EnvironmentConfig.for_dev/staging/prod)
├── stacks/
│   ├── foundation/        # Layer 1: NetworkStack, IamStack
│   ├── data/              # Layer 2: DatabaseStack, StorageStack, FsxLustreStack
│   ├── compute/           # Layer 3: EksStack, SagemakerHyperPodStack
│   └── networking/        # Layer 5: AlbStack
├── cdk_constructs/        # 可复用 L3 Construct
├── utils/                 # 工具函数
└── tests/                 # 测试
```

---

## Stack 模板 (简化版)

```python
class ExampleStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_config: EnvironmentConfig,
        vpc: ec2.IVpc,  # 依赖注入
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._env_config = env_config
        self._create_resources(vpc)
        apply_standard_tags(self, env_config)

    def _create_resources(self, vpc: ec2.IVpc) -> None:
        """私有方法创建资源"""
        pass

    @property
    def resource(self) -> SomeType:
        """公开属性导出资源"""
        return self._resource
```

---

## 详细规范 (按需加载)

当需要深入了解特定主题时，使用 `@` 引用对应规范文件:

| 任务 | 规范文件 | 引用方式 |
|------|----------|----------|
| 新建 Stack | `.claude/rules/02-stack-design.md` | `@02-stack-design.md` |
| 新建 Construct | `.claude/rules/03-construct-design.md` | `@03-construct-design.md` |
| 配置管理 | `.claude/rules/04-configuration.md` | `@04-configuration.md` |
| 代码风格 | `.claude/rules/05-code-style.md` | `@05-code-style.md` |
| 编写测试 | `.claude/rules/06-testing.md` | `@06-testing.md` |
| 安全审查 | `.claude/rules/07-security.md` | `@07-security.md` |
| HyperPod 部署 | `.claude/rules/08-hyperpod.md` | `@08-hyperpod.md` |

---

## HyperPod 部署 (快速参考)

**前置条件**: `./resources/scripts/setup_helm_chart.sh`

**部署顺序**: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack → FsxLustreStack

**Add-ons**: Training Operator (PyTorchJob) + Kueue (队列) + Prometheus/Grafana

---

## VPC 设计

| 子网 | CIDR | 用途 |
|------|------|------|
| Public | /20 | NAT Gateway, ALB |
| PrivateApp | /19 | EKS 节点 (~1200 节点) |
| PrivateData | /20 (isolated) | Aurora, FSx |
