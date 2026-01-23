# CDK 工程规范索引

本目录包含 AWS CDK 项目的完整工程规范，用于指导 Claude Code 进行开发工作。

## 按需加载机制

大部分规范文件配置了 `paths` frontmatter，**仅在处理相关文件时才会加载**，节省上下文空间。

| 规范 | 触发路径 | 加载条件 |
|------|----------|----------|
| 02-stack-design | `stacks/**/*.py`, `app.py` | 编辑 Stack 代码时 |
| 03-construct-design | `cdk_constructs/**/*.py` | 编辑 Construct 时 |
| 04-configuration | `config/**/*.py`, `cdk.json` | 编辑配置时 |
| 06-testing | `tests/**/*.py` | 编写测试时 |
| 07-security | `stacks/**/*.py`, `utils/iam_*.py` | 安全相关代码时 |
| 08-hyperpod | `stacks/compute/*hyperpod*.py` | HyperPod 相关时 |

**始终加载**: `00-index.md`, `01-architecture.md`, `05-code-style.md`

> **参考文档**: Claude Code Memory 管理规范已移至 `docs/claude-code-memory-management.md`

## 规范文件

| 文件 | 内容 | 加载方式 |
|------|------|----------|
| [01-architecture.md](01-architecture.md) | 分层架构、目录结构、VPC 设计 | 🔵 始终 |
| [02-stack-design.md](02-stack-design.md) | Stack 结构模板、依赖注入、资源导出 | 🟢 按需 |
| [03-construct-design.md](03-construct-design.md) | L3 Construct 设计、Props 模式、Aspect | 🟢 按需 |
| [04-configuration.md](04-configuration.md) | 常量管理、环境配置、工厂方法 | 🟢 按需 |
| [05-code-style.md](05-code-style.md) | 代码风格、命名规范、类型注解 | 🔵 始终 |
| [06-testing.md](06-testing.md) | 测试分层、Fixtures、覆盖率目标 | 🟢 按需 |
| [07-security.md](07-security.md) | IAM、加密、网络安全、CDK Nag | 🟢 按需 |
| [08-hyperpod.md](08-hyperpod.md) | HyperPod 部署、Training Operator、FSx | 🟢 按需 |

## 快速参考

### 核心原则

1. **分层依赖**: 上层只依赖下层，禁止反向依赖
2. **依赖注入**: 通过构造函数参数传递资源
3. **配置驱动**: 所有环境差异通过配置控制
4. **最小权限**: IAM 策略只授予必要权限
5. **加密一切**: 静态和传输数据必须加密

### Stack 分层

```
Layer 1: NetworkStack, IamStack
Layer 2: DatabaseStack, StorageStack
Layer 3: EksStack → SagemakerHyperPodStack → HyperPodAddonsStack
Layer 4: FsxLustreStack
Layer 5: AlbStack
```

### 常用命令

```bash
# 开发
ruff check . && mypy .    # 代码检查
pytest -m unit            # 单元测试
cdk synth                 # 合成模板

# 部署
cdk deploy --context env=dev
cdk deploy --context env=staging
cdk deploy --context env=prod
```

### 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| Stack ID | PascalCase | `NetworkStack` |
| Construct ID | PascalCase | `MainVpc` |
| 资源名称 | kebab-case | `ai-platform-dev-vpc` |
| 方法 | snake_case | `_create_vpc()` |
| 常量 | UPPER_SNAKE | `MAX_NODES` |

### 环境配置

| 配置 | Dev | Staging | Prod |
|------|-----|---------|------|
| NAT | 1 | 2 | 2 |
| 多 AZ | ❌ | ✅ | ✅ |
| WAF | ❌ | ❌ | ✅ |
| 删除保护 | ❌ | ✅ | ✅ |
| CDK Nag | 跳过 | 启用 | 启用 |

## 使用指南

### 新建 Stack

1. 阅读 [01-architecture.md](01-architecture.md) 确定分层位置
2. 参考 [02-stack-design.md](02-stack-design.md) 使用模板
3. 遵循 [05-code-style.md](05-code-style.md) 编码规范
4. 按照 [06-testing.md](06-testing.md) 编写测试
5. 检查 [07-security.md](07-security.md) 安全要求

### 新建 Construct

1. 阅读 [03-construct-design.md](03-construct-design.md) 了解设计原则
2. 使用 Props dataclass 管理配置
3. 提供工厂函数简化使用
4. 编写完整的单元测试

### HyperPod 相关

1. 阅读 [08-hyperpod.md](08-hyperpod.md) 了解部署流程
2. 确保 Helm Chart 已下载
3. 注意 15 分钟超时设置
4. 配置正确的 GPU 实例组

## 维护说明

- 规范文件应与代码实现保持同步
- 重大变更需更新对应规范
- 新增模式需添加到对应规范文件
- 定期审查规范的时效性
