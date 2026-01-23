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

## 详细规范

`.claude/rules/` 目录中的规范文件**按需自动加载**:

| 规范 | 触发条件 |
|------|----------|
| 02-stack-design | 编辑 `stacks/**/*.py` |
| 03-construct-design | 编辑 `cdk_constructs/**/*.py` |
| 04-configuration | 编辑 `config/**/*.py` |
| 05-code-style | 编辑 `**/*.py` |
| 06-testing | 编辑 `tests/**/*.py` |
| 07-security | 编辑安全相关代码 |
| 08-hyperpod | 编辑 HyperPod 相关代码 |

**手动引用**: 在对话中使用 `@.claude/rules/02-stack-design.md` 加载特定规范

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
