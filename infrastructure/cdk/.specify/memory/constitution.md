<!--
  SYNC IMPACT REPORT
  ===================
  Version Change: N/A → 1.0.0 (Initial Creation)

  Modified Principles: None (initial version)

  Added Sections:
  - I. 分层架构优先 (Layer-First Architecture)
  - II. 强类型配置 (Strongly-Typed Configuration)
  - III. 安全即代码 (Security as Code)
  - IV. 环境一致性 (Environment Consistency)
  - V. 代码质量门禁 (Code Quality Gates)
  - AWS Well-Architected 约束
  - 开发工作流
  - 治理规则

  Removed Sections: None (initial version)

  Templates Status:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ Compatible
  - .specify/templates/tasks-template.md: ✅ Compatible

  Follow-up TODOs: None
-->

# AI Training Platform CDK Infrastructure Constitution

## Core Principles

### I. 分层架构优先 (Layer-First Architecture)

所有基础设施变更 MUST 遵循既定的 Stack 分层依赖顺序：

```
Layer 1 (Foundation):  NetworkStack, IamStack (并行)
                            ↓
Layer 2 (Data):        DatabaseStack, StorageStack (并行)
                            ↓
Layer 3a (Compute):    EksStack
                            ↓
Layer 3b (HyperPod):   SagemakerHyperPodStack
                            ↓
Layer 4 (Storage):     FsxLustreStack
                            ↓
Layer 5 (Ingress):     AlbStack
```

**规则**：
- 新增 Stack MUST 明确其在分层中的位置
- Stack 间依赖 MUST 通过 `add_dependency()` 显式声明
- 跨层引用 MUST 使用导出值或 Props 传递，禁止硬编码 ARN
- 循环依赖是禁止的（CDK 会检测并报错）

**理由**：分层架构确保基础设施的部署顺序可预测，便于增量部署和故障隔离。

### II. 强类型配置 (Strongly-Typed Configuration)

所有环境配置 MUST 使用 dataclass 定义，禁止松散的字典或环境变量直接使用。

**规则**：
- 配置类 MUST 使用 `@dataclass(frozen=True)` 确保不可变性
- 配置参数 MUST 有类型注解和默认值
- 新环境配置 MUST 通过工厂方法创建（如 `for_dev()`, `for_staging()`, `for_prod()`）
- 敏感配置 MUST 通过 CDK context 或 Secrets Manager 传递，禁止硬编码

**理由**：强类型配置提供编译时验证、IDE 自动补全，并确保环境间配置的一致性。

### III. 安全即代码 (Security as Code)

安全检查 MUST 集成到 CDK 合成阶段，不依赖部署后审计。

**规则**：
- staging/prod 环境 MUST 启用 CDK Nag (`AwsSolutionsChecks`)
- CDK Nag 抑制 MUST 在 `app.py` 中集中定义，并附带明确的 `reason` 说明
- 新增 Stack MUST 评估 CDK Nag 规则并处理所有警告
- IAM 策略 MUST 遵循最小权限原则，禁止使用 `*` 通配符 Action（资源通配符需说明理由）
- KMS 加密 MUST 用于所有数据存储（S3、Aurora、FSx）

**理由**：安全问题在开发阶段发现的成本远低于生产环境，CDK Nag 提供自动化的 Well-Architected 合规检查。

### IV. 环境一致性 (Environment Consistency)

所有三个环境（dev/staging/prod）MUST 使用相同的 Stack 代码，仅通过配置参数区分。

**规则**：
- 环境差异 MUST 通过 `EnvironmentConfig` 参数控制，禁止环境特定的 if/else 分支（除非涉及可选功能开关）
- 资源命名 MUST 使用 `{resource_prefix}-{resource-name}` 格式（如 `ai-platform-dev-network`）
- 标签 MUST 包含：`Project`, `Environment`, `ManagedBy`, `CostCenter`
- 环境升级路径：dev → staging → prod，禁止跳过 staging 直接部署 prod

**理由**：环境一致性减少"在我机器上能跑"问题，确保 staging 是 prod 的真实预演。

### V. 代码质量门禁 (Code Quality Gates)

所有代码变更 MUST 通过以下自动化检查：

**规则**：
- `ruff check .` MUST 通过（零错误、零警告）
- `ruff format .` MUST 应用（代码格式化）
- `mypy .` MUST 通过（严格模式，零类型错误）
- `pytest` MUST 通过所有单元测试
- `cdk synth` MUST 成功生成 CloudFormation 模板

**合并前检查清单**：
```bash
ruff check . && ruff format . && mypy . && pytest && cdk synth
```

**理由**：自动化质量门禁确保代码库的一致性和可维护性，减少 CR 中关于格式的争论。

## AWS Well-Architected 约束

### 网络安全
- VPC MUST 使用 3 层子网隔离（Public/PrivateApp/PrivateData）
- 数据层子网 MUST 是隔离子网（无 NAT Gateway 出口）
- VPC 终端节点 MUST 用于 AWS 服务访问（S3、ECR、STS 等）
- 安全组 MUST 使用最小开放原则，禁止 0.0.0.0/0 入站（ALB 除外）

### 数据保护
- Aurora MUST 启用自动备份（dev: 7天，prod: 14天）
- S3 存储桶 MUST 启用版本控制和生命周期策略
- 所有传输中数据 MUST 使用 TLS 1.2+
- FSx for Lustre MUST 使用 S3 Data Repository Association 进行数据同步

### 高可用性
- prod 环境 MUST 使用 Multi-AZ 部署
- NAT Gateway MUST 至少 2 个（prod）以避免单点故障
- Aurora MUST 启用 Serverless v2 自动扩缩容
- EKS 节点组 MUST 跨多个 AZ 分布

### 成本优化
- dev 环境 SHOULD 使用单 NAT Gateway
- dev 环境 Aurora SHOULD 配置 min_acu=0.5 允许暂停
- 检查点存储 MUST 配置生命周期策略（30天后转 Standard-IA）

## 开发工作流

### Stack 开发流程
1. 在 `stacks/` 创建新 Stack 文件
2. 在 `app.py` 中实例化并声明依赖
3. 运行 `cdk synth` 验证模板生成
4. 添加 CDK Nag 抑制（如需要）
5. 编写单元测试验证 Stack 属性
6. 提交 PR 并通过所有质量门禁

### 配置扩展流程
1. 在 `config/environments.py` 添加新配置类或字段
2. 更新 `VpcConfig`/`DatabaseConfig`/`StorageConfig`/`EksConfig` dataclass
3. 更新工厂方法 `for_dev()`, `for_staging()`, `for_prod()`
4. 在 Stack 中使用 `env_config.xxx` 访问配置

### 部署流程
```bash
# 开发环境（本地）
cdk deploy --context env=dev

# staging 环境（CI/CD 或手动）
cdk deploy --context env=staging

# 生产环境（仅通过 CI/CD）
cdk deploy --context env=prod --context account=PROD_ACCOUNT --context region=REGION
```

## Governance

### 修订程序
1. 提出 Constitution 修订的 PR
2. 至少一名团队成员审核
3. 更新版本号（遵循语义化版本）
4. 同步更新依赖此 Constitution 的模板文件
5. 通知团队成员新规则生效

### 版本策略
- **MAJOR**: 核心原则的删除或重大重定义
- **MINOR**: 新增原则、章节或重大指南扩展
- **PATCH**: 措辞澄清、拼写修正、非语义性改进

### 合规审查
- 所有 PR MUST 验证是否符合 Constitution 原则
- 复杂度增加 MUST 有合理理由（记录在 PR 描述中）
- 违反原则的例外 MUST 在 PR 中明确标注并获得批准

**Version**: 1.0.0 | **Ratified**: 2025-01-10 | **Last Amended**: 2025-01-10
