<!--
===============================================================================
SYNC IMPACT REPORT
===============================================================================
Version change: 1.7.5 → 1.7.6 (Current)
Version bump rationale: PATCH - 修正 SDK 优先原则的核心定义,明确原则目的是"避免重复造轮子",正确定位 sagemaker-hyperpod SDK 的适用范围

Modified principles:
  - I.B SDK 优先 (SDK-First)
    * 修正核心原则定义: "尽可能使用 SDK 简化代码实现,避免重复造轮子"
    * 正确定位 sagemaker-hyperpod SDK 为 HyperPod 四大功能模块的专用 SDK (而非泛化的"首选 SDK")
    * 重构决策流程: 按功能域选择合适的 SDK,而非按 SDK 排列优先级
    * 新增 sagemaker-hyperpod SDK 适用范围说明 (Cluster, Training, Inference, Space)
    * 明确不同功能域的 SDK 选择指南

Benefits:
  - 原则目的更加清晰: 核心是避免重复造轮子
  - 正确反映 sagemaker-hyperpod SDK 的定位: HyperPod 功能专用,非通用首选
  - 消除团队对 SDK 选择的困惑: 按功能域选择而非按优先级排列
  - 与官方文档一致: sagemaker-hyperpod SDK 明确支持 Cluster/Training/Inference/Space

Templates requiring updates:
  ✅ .specify/templates/plan-template.md - 无需更新 (原则引用不变,描述更准确)
  ✅ .specify/templates/spec-template.md - 无需更新 (原则引用不变)
  ✅ .specify/templates/tasks-template.md - 无需更新 (原则引用不变)

Follow-up TODOs:
  - 无新增 TODO (本次为修正性澄清,不影响现有引用)

===============================================================================
Previous Version History:
===============================================================================
Version 1.7.5 (2026-01-03):
  - PATCH: 重构 SDK 优先级为四级体系 (后续被 1.7.6 修正)

Version 1.7.4 (2026-01-03):
  - PATCH: 明确原则边界、统一格式和术语、消除交叉引用、添加术语表、补充技术互斥性约束
  - 修正 Principle X 中的 SDK 引用为 "Principle I.B"
  - 添加 Glossary 术语表章节
  - 添加 Elastic Training vs Checkpointless Training 互斥性约束

Version 1.7.0 (2026-01-03):
  - MINOR: 合并重叠原则 (I, II, XI → I),减少原则数量 13→11
  - 添加 Elastic Training 互斥性说明和决策树
  - 修正 HyperPod 组件分类
  - 添加5个 HyperPod 高级功能
===============================================================================
-->

# AI Studio Platform Constitution

企业级 AI 平台 - 统一模型开发、训练、部署平台

## 愿景声明

构建一个统一的企业级 AI 平台,赋能各业务部门自助式模型开发、训练和部署能力。
平台以 **AWS SageMaker HyperPod 结合 Amazon EKS** 作为核心基础设施,提供可扩展、
高性价比、企业就绪的 AI/ML 运营能力,全面提升企业 AI 模型开发上线效率。

## Glossary (术语表)

### 核心技术术语

**AWS SageMaker HyperPod**
- AWS 提供的专为大规模 AI/ML 训练优化的托管基础设施
- 基于 Amazon EKS 构建,提供深度健康检查、自动恢复、弹性训练等企业级能力

**EKS (Amazon Elastic Kubernetes Service)**
- AWS 托管的 Kubernetes 服务
- HyperPod 的编排层,提供容器编排和资源管理

**EKS 托管 Add-ons**
- 通过 EKS 控制台/API 直接安装和管理的附加组件
- 由 AWS 维护和升级,无需手动配置
- 示例: HyperPod Training Operator, Task Governance, Observability Add-on

**Kubernetes 生态兼容组件**
- 标准开源 Kubernetes 组件,可在 HyperPod EKS 集群中部署
- 需要手动安装和配置,但与 Kubernetes 生态完全兼容
- 示例: Kubeflow Training Operator, Argo Workflows

**HyperPod SDK (sagemaker-hyperpod)**
- AWS 官方 Python SDK,用于与 HyperPod 交互
- 提供集群管理、训练任务、推理部署、开发空间的高层抽象 API

**HyperPod 原生能力**
- HyperPod 特有的扩展功能,超越标准 Kubernetes 能力
- 包括: Checkpointless Training (无检查点训练), Elastic Training (弹性训练), Deep Health Checks (深度健康检查), Automatic Node Recovery (自动节点恢复)

### 缩写对照表

| 缩写 | 全称 | 说明 |
|------|------|------|
| EKS | Amazon Elastic Kubernetes Service | AWS 托管 Kubernetes |
| K8S | Kubernetes | 容器编排平台 (K-ubernete-S, 中间8个字母) |
| MIG | Multi-Instance GPU | NVIDIA GPU 分区技术 |
| SDK | Software Development Kit | 软件开发工具包 |
| API | Application Programming Interface | 应用程序接口 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| IAM | Identity and Access Management | AWS 身份和访问管理 |
| CSI | Container Storage Interface | 容器存储接口 |
| IaC | Infrastructure as Code | 基础设施即代码 |
| MLflow | Machine Learning Flow | ML 实验追踪平台 |
| TDD | Test-Driven Development | 测试驱动开发 |
| SOLID | Software Design Principles | 软件设计原则 (SRP, OCP, LSP, ISP, DIP) |
| NFR | Non-Functional Requirement | 非功能性需求 |

## Core Principles

### I. HyperPod Native Architecture (HyperPod 原生架构)

平台 MUST 采用 AWS SageMaker HyperPod with EKS 作为核心基础设施，
遵循原生优先、SDK 优先的开发原则。

#### A. 组件优先级 (Component Priority)

所有平台功能 MUST 按照以下优先级选择技术组件:

1. **首选**: EKS 托管 Add-ons 和 HyperPod 原生能力
   - HyperPod Training Operator - 分布式训练任务管理
   - HyperPod Inference Operator - 模型服务部署
   - HyperPod Task Governance - 配额管理和任务调度
   - HyperPod Observability Add-on - Prometheus/Grafana 集成
   - HyperPod Elastic Agent - 弹性训练和无检查点训练
   - Amazon SageMaker Spaces Add-on - JupyterLab/VS Code IDE
   - cert-manager - 证书管理 (Training Operator 必需依赖)

2. **次选**: AWS 托管服务
   - SageMaker Model Registry - 模型版本控制和治理
   - SageMaker Managed MLflow - ML 实验追踪
   - FSx for Lustre, EFS, S3 - 存储服务

3. **第三选**: Kubernetes 生态兼容组件
   - 仅在 HyperPod 不提供对应功能时使用
   - 例: Argo Workflows (流水线编排)

4. **避免**: 自行实现 HyperPod 已提供的功能

**技术架构约束**:
- 采用 Amazon EKS 作为编排层 (HyperPod 基于 EKS 构建)
- 平台设计以 HyperPod 扩展能力为核心,不要求与开源 K8S 生态完全兼容
- 工作负载 MAY 使用 HyperPod 特有的扩展功能 (如 Checkpointless Training, Elastic Agent)
- 允许使用 kubectl、Helm 等 K8S 工具进行管理 (但主要通过 HyperPod SDK 和控制台)

#### B. SDK 优先 (SDK-First)

**核心原则**: 尽可能使用 SDK 简化代码实现,避免重复造轮子。

所有平台功能实现 MUST 按照以下决策流程选择实现方式:

1. **优先使用官方 SDK** (如果 SDK 支持该功能)
   - **HyperPod 功能** → 使用 `sagemaker-hyperpod` SDK (见下方适用范围)
   - **AWS 服务集成** (S3, SQS, SNS, CloudWatch, IAM 等) → 使用 boto3 或其他 AWS SDK
   - **Kubernetes 原生操作** → 使用 kubernetes-client

2. **次选成熟的开源库** (如果官方 SDK 不支持)
   - 社区广泛使用且维护活跃的库
   - 标准化接口和跨平台兼容需求

3. **最后自行实现** (仅在以上方式均无法满足需求时)
   - MUST 提交例外申请并获得平台治理委员会批准
   - MUST 在代码中明确注释说明自行实现的原因

**sagemaker-hyperpod SDK 适用范围**:

`sagemaker-hyperpod` SDK 是 AWS 官方为 HyperPod 提供的 Python SDK,专门用于以下四大功能模块:

| 功能模块 | 适用场景 | SDK 模块 |
|---------|---------|---------|
| **Cluster Management** | 集群连接、配置、监控、生命周期管理 | `sagemaker.hyperpod.cluster` |
| **Training** | 训练任务提交、状态监控、生命周期管理 (PyTorch, TensorFlow, MPI 等) | `sagemaker.hyperpod.training` |
| **Inference** | 模型端点创建、扩缩容、健康检查、JumpStart 模型部署 | `sagemaker.hyperpod.inference` |
| **Space** | JupyterLab/VS Code IDE 的创建、配置和生命周期管理 | `sagemaker.hyperpod.space` |

**实施要求**:
- 开发 HyperPod 相关功能前 MUST 首先查阅 `sagemaker-hyperpod` SDK 文档确认是否支持
- 开发 AWS 服务集成功能前 MUST 首先查阅 boto3 或相关 AWS SDK 文档
- 代码审查 MUST 验证 SDK 选择的合理性 (按功能域选择合适的 SDK)
- 如需绕过 SDK 直接使用底层 API,MUST 在 PR 中说明理由
- 平台 API 设计 SHOULD 与相关 SDK 保持一致的抽象层级和术语

#### C. 例外处理 (Exception Handling)

- 需要使用非原生组件时，MUST 提交例外申请
- 经平台治理委员会批准后方可实施
- 例外 MUST 记录技术理由和有效期
- 定期复审例外的必要性

**理由**:
1. **深度集成**: 原生组件与 HyperPod 基础设施深度集成,提供最佳的弹性恢复、自动扩缩和故障处理能力
2. **降低成本**: 减少自定义开发和维护成本,避免重复造轮子
3. **持续更新**: 确保与 AWS 服务更新保持同步,获得持续的技术支持
4. **企业优化**: HyperPod 提供了超越标准 Kubernetes 的企业级 AI/ML 功能和深度优化
5. **开发效率**: SDK 提供高层抽象,简化开发流程,减少样板代码

**参考文档**: https://sagemaker-hyperpod-cli.readthedocs.io/

### II. Multi-Tenant Resource Governance (多租户资源治理)

平台 MUST 支持企业级多租户资源隔离和治理:

- MUST 通过 HyperPod Task Governance 为不同业务部门/项目设置计算配额
- MUST 支持基于优先级的任务调度 (使用 Kueue 进行队列管理)
- MUST 实现细粒度的 GPU/vCPU/内存配额分配
- MUST 提供资源使用报告和成本归属能力
- SHOULD 支持配额借用和空闲资源共享策略

**理由**: 企业 AI 平台需服务多个业务部门,必须确保资源公平分配、成本可追溯、
高优先级任务得到保障。

### III. Full Lifecycle Observability (全生命周期可观测)

平台 MUST 提供从开发到生产的全链路可观测能力:

- 集群级监控: GPU 利用率、节点健康、网络性能 (NVIDIA DCGM, EFA metrics)
- 任务级监控: 训练进度、队列状态、资源消耗
- 推理级监控: 延迟、吞吐、错误率、Token 级指标
- 实验管理: 集成 MLflow 进行实验追踪和模型管理
- 统一仪表板: 通过 Amazon Managed Grafana 提供可视化

**理由**: 大规模 AI 开发需要深入的可观测性来诊断问题、优化性能、控制成本。

### IV. Resilience and Auto-Recovery (弹性与自动恢复)

平台 MUST 充分利用 HyperPod 的弹性基础设施能力:

- 启用深度健康检查 (Deep Health Checks) 检测 GPU 和网络问题
- 启用自动节点恢复 (Automatic Node Recovery) 处理硬件故障
- 支持训练任务自动恢复 (Job Auto-Resume) 使用 Checkpointing
- MUST 配置分层检查点存储 (Tiered Checkpointing) 优化检查点性能

**弹性训练技术选择 (MUST 选择其一,两者互斥)**:

| 技术方案 | 适用场景 | 支持特性 | 限制 |
|---------|---------|---------|-----|
| **Elastic Training** | 需要动态扩缩容的长时间训练任务 | ✅ 自动扩缩容<br>✅ DDP, FSDP, PyTorch DCP<br>✅ Checkpointing | ❌ 不支持 Checkpointless Training<br>❌ 不支持 Spot Instances |
| **Checkpointless Training** | 需要最快故障恢复的训练任务 | ✅ 无检查点自动恢复<br>✅ 秒级故障恢复<br>✅ 减少存储 I/O | ❌ 不支持 Elastic Training<br>❌ 不支持动态扩缩容 |

**决策树**:
```
训练任务类型选择:
│
├─ 需要弹性扩缩容 (根据负载动态调整节点数)?
│   └─ 是 → 使用 Elastic Training
│         ├─ 支持: DDP, FSDP, PyTorch DCP
│         ├─ 需要: Checkpointing 配置
│         └─ 不支持: Checkpointless Training, Spot Instances
│
└─ 需要最快故障恢复 (秒级恢复,无检查点开销)?
    └─ 是 → 使用 Checkpointless Training
          ├─ 支持: 自动故障恢复,无检查点 I/O
          └─ 不支持: Elastic Training, 动态扩缩容
```

**注意事项**:
- ⚠️ **互斥性**: Elastic Training 和 Checkpointless Training 不能同时使用
- 如果既需要弹性扩缩容又需要快速恢复,优先选择 Elastic Training + 优化 Checkpointing 策略
- 对于非关键实验性训练,可使用标准 Checkpointing + Spot Instances 降低成本

**理由**: 大规模 AI 训练任务运行时间长,硬件故障不可避免;自动恢复能力可将训练
goodput 提升至 95% 以上,显著降低资源浪费。

### V. Security and Compliance (安全与合规)

平台 MUST 满足企业级安全要求:

- 外部入口和 API 通信 MUST 使用 TLS 1.2+ 加密;集群内部通信依赖 VPC 网络隔离和 Nitro 硬件级加密保护
- 支持 VPC 隔离和私有端点访问
- 集成 IAM 和 Kubernetes RBAC 进行细粒度权限控制
- 支持使用客户管理的 KMS 密钥进行数据加密
- MUST 记录所有安全相关事件和访问日志
- SHOULD 支持合规审计和资源标签策略

**理由**: 企业 AI 平台处理敏感数据和模型,必须满足数据安全、访问控制和审计追溯的要求。

### VI. Platform First (平台优先)

企业 AI 平台 MUST 作为统一、内聚的平台构建,而非零散工具的集合:

- 所有功能 MUST 集成到具有共享标准的通用架构中
- 每个组件 MUST 支持更广泛的平台能力,而非孤立运行
- 平台 MUST 维护集中治理、标准和基础设施

**理由**: 碎片化的工具集会造成运维开销、不一致的用户体验和维护负担,
从而削弱企业采用率。

### VII. Model Lifecycle Management (模型生命周期管理)

所有模型 MUST 遵循从开发到部署到监控的标准化生命周期:

- 模型的版本控制、追踪和可审计性不可协商
- 每个模型 MUST 保持训练数据、代码、参数和部署目标之间的清晰血缘关系
- 使用 SageMaker Model Registry 进行模型版本控制和审批工作流
- MLflow 集成用于实验追踪
- 生产部署前的自动化模型验证关卡
- 明确的制品存储和保留策略

**理由**: 标准化的模型生命周期管理确保模型质量、可追溯性和合规性。

### VIII. Infrastructure as Code Excellence (基础设施即代码卓越)

所有基础设施 MUST 通过基础设施即代码 (IaC) 实践进行定义、版本控制和部署:

- 禁止在生产环境中进行手动基础设施变更
- 基础设施代码 MUST 与应用代码接受同等严格的审查
- 使用 AWS CDK 进行基础设施配置(TypeScript 或 Python)
- 使用 EKS 托管 ArgoCD 的 GitOps 工作流进行集群配置
- 使用 Helm charts 进行应用部署标准化
- 版本控制的集群蓝图和附加组件配置
- 自动化漂移检测和修复

**理由**: IaC 确保基础设施的一致性、可重复性和可审计性,减少人为错误和配置漂移。

### IX. Test Strategy and Quality Assurance (测试策略与质量保证)

平台所有核心功能 MUST 具备全面的自动化测试覆盖,确保系统质量和可靠性:

**测试金字塔策略**:
- **单元测试 (最多数量)**: MUST 覆盖所有业务逻辑、服务层和工具函数
  - 目标覆盖率: 后端 ≥70%, 前端组件 ≥60%
  - MUST 独立运行,无外部依赖
  - 执行速度: 全部单元测试 <2分钟
- **集成测试 (中等数量)**: MUST 覆盖所有 API 端点和组件协作
  - 目标覆盖率: 所有 REST API 端点 100%
  - MUST 测试数据库交互、外部服务集成
  - 执行速度: 全部集成测试 <5分钟
- **端到端测试 (少量关键场景)**: MUST 覆盖所有用户验收场景
  - 目标: 每个 User Story 至少1个完整端到端测试
  - MUST 验证关键用户旅程的完整性
  - 执行速度: 全部E2E测试 <15分钟

**测试覆盖率要求**:
- 核心功能 (P1 User Stories): MUST 达到 80%+ 代码覆盖率
- 次要功能 (P2 User Stories): SHOULD 达到 70%+ 代码覆盖率
- 辅助功能 (P3 User Stories): SHOULD 达到 60%+ 代码覆盖率
- 关键路径功能 (训练任务管理、资源调度、检查点恢复): MUST 达到 90%+ 覆盖率

**测试开发原则**:
- MUST 采用测试驱动开发 (TDD) 方法: 先写测试,确保失败,再实现功能
- 新增功能 MUST 包含相应的测试用例,否则不允许合并
- 代码审查 MUST 验证测试覆盖率和测试质量
- 破坏性变更 MUST 包含回归测试

**持续集成要求**:
- 所有测试 MUST 在 CI/CD 流水线中自动执行
- Pull Request MUST 通过所有测试才能合并
- 测试失败的代码 MUST NOT 部署到任何环境
- 每日构建 MUST 生成测试覆盖率报告

**性能和可靠性测试**:
- MUST 验证非功能性需求 (NFRs) 如响应时间、并发处理能力
- 关键服务 MUST 包含负载测试和压力测试
- 灾难恢复场景 MUST 包含故障注入测试
- 目标可用性 99.9% MUST 通过可靠性测试验证

**理由**: 完善的测试覆盖是确保企业级 AI 平台质量、可靠性和可维护性的基石。
缺乏测试的代码存在高回归风险,会导致生产故障、用户体验下降和维护成本增加。

### X. Code Design and Implementation Quality (代码设计与实现质量)

所有代码 MUST 遵循软件工程最佳实践,确保代码质量、可维护性和长期演进能力:

**软件设计原则 (SOLID + DRY, KISS, YAGNI)**:
- **单一职责原则 (SRP)**: 每个类/函数只负责一个功能,只有一个修改理由
- **开闭原则 (OCP)**: 对扩展开放,对修改封闭
- **里氏替换原则 (LSP)**: 子类可以替换父类而不影响程序正确性
- **接口隔离原则 (ISP)**: 客户端不应依赖它不需要的接口
- **依赖倒置原则 (DIP)**: 依赖抽象而非具体实现
- **DRY (Don't Repeat Yourself)**: 避免重复代码,提取公共功能
- **KISS (Keep It Simple, Stupid)**: 优先选择简单的设计方案
- **YAGNI (You Aren't Gonna Need It)**: 只实现当前需要的功能,不做过度设计

**代码整洁之道 (Clean Code)**:
- **命名清晰**: 变量、函数、类名必须清晰表达意图,避免缩写和模糊命名
- **函数精简**: 单个函数不超过50行,复杂函数必须拆分
- **参数控制**: 函数参数不超过3个,超过则使用对象封装
- **注释适度**: 代码应自解释,注释仅用于解释"为什么"而非"做什么"
- **错误处理**: 使用异常而非错误码,避免返回 null
- **格式一致**: 遵循项目代码风格指南 (Black for Python, ESLint for TypeScript)

**组件复用优先**:
- **MUST 优先使用成熟的SDK和第三方库**,避免重复造轮子
- **MUST 优先使用 HyperPod SDK** 而非自行实现 (如 Principle I.B 所述)
- **MUST 优先使用官方推荐的库**: FastAPI、SQLAlchemy、Pydantic、pytest (Python)
- **MUST 优先使用生态成熟的组件**: React、TypeScript、Zustand、TanStack Query (前端)
- **仅在以下情况自行实现**:
  - 现有库明确不支持业务需求
  - 现有库存在严重性能或安全问题
  - 轻量级工具函数 (<50行代码)

**代码审查和测试要求**:
- 所有代码 MUST 通过代码审查才能合并
- 审查必须验证: SOLID 原则遵循、代码整洁度、组件复用合理性
- 复杂业务逻辑 MUST 包含单元测试,目标覆盖率:
  - 核心功能 (P1 User Stories): ≥80%
  - 次要功能 (P2 User Stories): ≥70%
  - 辅助功能 (P3 User Stories): ≥60%
- 新增依赖 MUST 在 PR 中说明理由和评估替代方案

**技术债务管理**:
- 发现技术债务 MUST 记录在 TODO 或 Issue 中
- 严重技术债务 (影响性能、安全、可维护性) MUST 优先修复
- 不允许为了短期交付而故意引入技术债务

**理由**: 代码质量直接影响系统的长期可维护性、演进能力和团队生产力。遵循软件工程
最佳实践和代码整洁之道,可以减少bug、降低维护成本、提升开发效率。优先使用成熟的
SDK和组件可以避免重复造轮子,利用社区智慧,获得持续更新和技术支持,显著降低开发
和维护负担。

### XI. UI/UX Consistency (UI/UX 一致性)

平台UI/UX设计 MUST 与 AWS Console 保持一致,确保用户体验流畅、专业且符合AWS生态标准:

**AWS Console 设计对齐**:
- **MUST 使用 AWS Cloudscape Design System** 作为唯一UI组件库
- MUST 遵循 AWS Console 的设计语言、视觉规范和交互模式
- MUST 参考 AWS Console 现有服务的界面设计和用户旅程
- MAY 参考 AWS SageMaker Console、AWS EKS Console 的设计模式
- MUST 保持与 AWS 生态其他服务的一致用户体验

**视觉一致性**:
- **颜色方案**: 使用 Cloudscape 预定义的颜色系统 (主题色、辅助色、状态色)
- **字体系统**: 遵循 Cloudscape 字体规范 (Amazon Ember 字体族)
- **图标库**: 使用 Cloudscape 官方图标集,保持图标风格统一
- **间距系统**: 遵循 Cloudscape 的间距规范和栅格系统

**交互一致性**:
- **操作模式**: 按钮位置、操作流程、快捷键遵循 AWS Console 标准
- **反馈机制**: 加载状态、成功提示、错误提示使用 Cloudscape 标准组件
- **表单规范**: 输入框、下拉选择、日期选择等表单组件行为与 AWS Console 一致
- **导航模式**: 面包屑、侧边导航、顶部导航遵循 AWS Console 导航模式

**术语一致性**:
- **MUST 使用 AWS 官方术语**: 如 "Training Job" (而非 Job/Task)、"Model" (而非 Artifact)
- **MUST 遵循 AWS 命名规范**: 资源命名、操作动词、状态描述与 AWS 服务保持一致
- **MUST 建立术语词典**: 记录所有业务术语及其对应的 AWS 官方术语

**实施要求**:
- MUST 安装并使用 `@cloudscape-design/components` 和 `@cloudscape-design/global-styles`
- MUST 建立 Cloudscape 组件使用指南和最佳实践文档
- 新增UI组件 MUST 优先从 Cloudscape 选择,不得自行实现已有组件
- MUST 使用 Cloudscape 的布局组件 (AppLayout, ContentLayout, Grid, SpaceBetween)
- SHOULD 使用 Storybook 维护 Cloudscape 组件库文档和使用示例

**无障碍访问 (Accessibility)**:
- MUST 遵循 WCAG 2.1 AA 级别标准
- Cloudscape 组件已内置无障碍支持,MUST 正确使用其无障碍属性
- MUST 提供键盘导航支持,确保所有功能可通过键盘操作
- MUST 提供适当的 ARIA 标签和语义化 HTML 结构

**理由**: 与 AWS Console 保持一致的UI/UX设计可以:
1. **降低学习成本**: 用户无需学习新的交互模式,可快速上手
2. **提升专业形象**: 遵循 AWS 设计标准,增强平台可信度和专业性
3. **减少开发成本**: 使用成熟的 Cloudscape 组件库,避免重复造轮子
4. **确保无障碍访问**: Cloudscape 内置 WCAG 2.1 AA 支持,降低合规风险
5. **统一生态体验**: 与 AWS 其他服务保持一致,提供无缝的跨服务用户体验

**参考文档**:
- Cloudscape Design System: https://cloudscape.design/
- AWS Console UX Guidelines: https://aws.amazon.com/console/

## Technology Constraints

### 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 基础设施 | AWS SageMaker HyperPod with EKS | 弹性 AI 基础设施 |
| SDK | sagemaker-hyperpod Python SDK | 官方 Python SDK (MUST 优先使用) |
| 编排层 | Amazon EKS | Kubernetes 编排 |
| 训练 Operator | HyperPod Training Operator | 分布式训练管理 |
| 推理 Operator | HyperPod Inference Operator | 模型部署和服务 |
| 资源治理 | HyperPod Task Governance (Kueue) | 配额和调度 |
| 弹性训练 | HyperPod Elastic Agent | 弹性训练和无检查点训练 |
| 可观测性 | HyperPod Observability Add-on | Prometheus + Grafana |
| IDE 环境 | Amazon SageMaker Spaces Add-on | JupyterLab, VS Code |
| 实验管理 | Amazon SageMaker Managed MLflow (托管服务) | ML 实验追踪 |
| 模型注册 | SageMaker Model Registry | 模型版本控制和治理 |
| 流水线编排 | Argo Workflows (自行部署) | ML 工作流自动化 |
| 存储 | Amazon FSx for Lustre, Amazon S3, EFS | 高性能存储 |
| 容器镜像 | Amazon ECR | 镜像仓库 |
| 日志 | Fluent Bit + OpenSearch | 集中式日志聚合 |
| **UI 组件库** | **AWS Cloudscape Design System** | **AWS Console 官方设计系统 (MUST 使用)** |

### Kubernetes 生态兼容组件

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Training Operator | Kubeflow Training Operator | PyTorchJob、TFJob 等 Kubernetes 原生训练 |

### EKS 集成要求

- EKS 集群版本 MUST 保持在最新版本的两个小版本以内
- 支持的 Kubernetes 版本: 1.32、1.33、1.34
- 标准工作负载使用托管节点组,GPU/特殊实例使用自管理节点组
- 使用 HyperPod 托管 Karpenter 进行动态节点自动伸缩
- AWS Load Balancer Controller 用于入口管理
- EBS CSI 驱动和 EFS CSI 驱动用于持久化存储
- FSx for Lustre CSI 驱动用于高性能训练数据访问
- 使用 Pod Identity 或 IRSA 从 Pod 安全访问 AWS 服务

### HyperPod 集群管理

**EKS 托管 Add-ons** (通过 EKS 控制台/API 安装):
- HyperPod Training Operator - 分布式训练管理
- HyperPod Task Governance - 资源配额和调度 (基于 Kueue)
- HyperPod Observability Add-on - 监控和可观测性 (Prometheus + Grafana)
- HyperPod Elastic Agent - 弹性训练和无检查点训练支持
- Amazon SageMaker Spaces Add-on - IDE 和 Notebooks 开发环境 (JupyterLab/VS Code)
- cert-manager - 证书管理 (Training Operator 前置依赖)
- EKS Pod Identity Agent - 安全凭证管理

**需手动配置的组件** (需额外的 IAM 角色、策略、RBAC 配置):
- HyperPod Inference Operator - 模型推理部署
  - 需要配置: IAM 角色、IAM 策略、Kubernetes RBAC
  - 安装方式: 需按照 AWS 文档进行特定设置流程
- AWS Load Balancer Controller - 入口负载均衡管理
- FSx CSI Driver - FSx for Lustre 高性能存储访问
- KEDA (可选) - 基于事件驱动的自动扩缩容

**集群运维要求**:
- 使用最新 HyperPod AMI 版本(通过 UpdateClusterSoftware API 升级)
- 启用健康监控和自动实例替换
- 可复现环境的集群配置模板
- 支持多节点分布式训练模式
- 支持弹性训练(Elastic Training)和无检查点训练(Checkpointless Training)

### HyperPod 高级功能

**GPU 分区 (Multi-Instance GPU / MIG)**:
- **描述**: 使用 NVIDIA MIG 技术将单个 GPU 分区为多个独立的计算单元
- **适用场景**:
  - 推理工作负载 (多个小模型共享单个 GPU)
  - 开发和实验环境 (降低单用户 GPU 成本)
  - 小规模模型训练和调试
- **配置要求**:
  - 支持的实例类型: p4d.24xlarge (A100), p5.48xlarge (H100)
  - 需要在 HyperPod 节点配置中启用 MIG 模式
  - 可配置分区大小: 1g.5gb, 2g.10gb, 3g.20gb, 4g.20gb, 7g.40gb (A100)
- **使用建议**: SHOULD 用于推理和开发环境,降低资源成本;训练任务通常使用完整 GPU

**托管分层 KV 缓存 (Tiered KV Cache)**:
- **描述**: 两层缓存架构 - L1 (本地内存) + L2 (节点级共享缓存)
- **适用场景**:
  - 高吞吐量 LLM 推理服务
  - 长上下文对话场景 (减少重复计算)
  - 多请求共享 KV 缓存的场景
- **配置选项**:
  - L1 缓存: GPU 内存或主机内存
  - L2 后端: Redis Cluster 或 HyperPod Tiered Storage
- **使用建议**: SHOULD 用于生产 LLM 推理端点,显著提升吞吐量和降低延迟

**智能路由 (Intelligent Routing)**:
- **描述**: 基于请求特征将请求路由到最优推理实例
- **路由策略**:
  - `prefix`: 根据 prompt 前缀匹配路由
  - `kv_cache`: 根据 KV 缓存命中率路由
  - `session`: 会话亲和性路由 (同一会话路由到同一实例)
  - `roundrobin`: 轮询负载均衡
- **适用场景**:
  - 多租户推理服务 (不同租户路由到不同实例)
  - KV 缓存优化 (提高缓存命中率)
  - 会话保持需求
- **使用建议**: SHOULD 用于多租户或需要缓存优化的推理场景

**HyperPod Spot Instances**:
- **描述**: 使用 EC2 Spot 容量降低计算成本 (可节省高达 90% 成本)
- **适用场景**:
  - 容错训练工作负载 (可接受中断)
  - 非紧急批处理任务
  - 实验性训练任务
- **注意事项**:
  - ⚠️ MUST 配合 Checkpointing 使用 (定期保存训练状态)
  - ⚠️ 不支持 Elastic Training (两者互斥)
  - ⚠️ 可能随时被中断,需要自动恢复机制
- **使用建议**: SHOULD 用于成本敏感的非关键训练任务

**MLflow 3.0 集成**:
- **新功能**:
  - **Tracing**: 端到端追踪 AI 应用执行流程 (LLM 调用链、提示词、输出)
  - **LoggedModel**: 统一追踪模型、trace、指标和参数
  - **Prompt Registry**: 提示词版本控制和管理
  - **Model Evaluation**: 内置模型评估和对比功能
- **配置要求**:
  - 使用 SageMaker Managed MLflow 最新版本
  - 启用 Tracing 功能需要配置 MLflow Tracking URI
- **适用场景**:
  - LLM 应用开发和调试 (追踪提示词和输出)
  - 多版本模型对比和评估
  - 提示词工程和优化
- **使用建议**: MUST 用于 LLM 应用开发,SHOULD 用于所有模型实验管理
- **参考文档**: https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html

### 禁止事项

- MUST NOT 使用 Slurm 编排 (本项目选择 EKS 路线)
- MUST NOT 绕过 Task Governance 直接提交无配额管理的作业
- MUST NOT 在生产环境禁用健康检查或自动恢复功能
- MUST NOT 使用非加密的通信通道
- MUST NOT 在 SDK 提供相同功能的情况下自行实现底层 K8S 交互
- **MUST NOT 使用 Cloudscape 以外的 UI 组件库** (如 MUI, Ant Design, Element Plus)
- **MUST NOT 自行实现 Cloudscape 已提供的 UI 组件**
- **MUST NOT 同时启用 Elastic Training 和 Checkpointless Training** (两者技术互斥,见 Principle IV)
- **MUST NOT 在未配置 Checkpointing 的情况下使用 Spot Instances** (训练中断时无法恢复,导致进度完全丢失)

### 明确排除

以下组件明确排除,优先使用 HyperPod 原生替代方案:

- **SageMaker Training Jobs**: 传统 SageMaker 功能,非 HyperPod 原生,使用 HyperPod Training Operator 替代
- **SageMaker Endpoints**: 传统 SageMaker 功能,非 HyperPod 原生,使用 HyperPod Inference Operator 替代(除非有特殊集成需求)
- **SageMaker Studio**: 使用 Amazon SageMaker Spaces Add-on 替代
- **SageMaker HyperPod with Slurm**: 本项目专注于纯 EKS 编排架构,不支持 Slurm 调度
- **非 AWS 官方 UI 组件库**: 如 Material-UI (MUI)、Ant Design、Element Plus 等,使用 Cloudscape 替代

**例外情况**: 仅在 HyperPod 原生组件和 SDK 无法满足特定需求时,经平台治理委员会批准后,
方可使用非原生组件或底层 API,并必须记录技术理由。UI 组件库不允许例外,必须使用 Cloudscape。

### 版本要求

- AWS SageMaker HyperPod with EKS 为快速迭代服务,实施前 MUST 查阅最新官方文档
- 遵循 AWS 发布的 Helm Chart 和 Add-on 版本建议
- `sagemaker-hyperpod` SDK 版本 MUST 保持在最新稳定版或最新版的一个小版本以内
- `@cloudscape-design/components` 版本 MUST 保持在最新稳定版

## Development Workflow

### 开发流程

1. **环境准备**: 使用 SageMaker Spaces 创建开发空间 (JupyterLab/VS Code)
2. **SDK 集成**: 安装并配置 `sagemaker-hyperpod` SDK,建立集群连接
3. **代码开发**: 在 IDE 中进行模型开发和实验
4. **实验追踪**: 使用 MLflow 记录实验参数和指标
5. **训练提交**: 通过 `sagemaker-hyperpod` SDK 提交训练任务
6. **监控验证**: 在 Grafana 仪表板监控训练进度
7. **模型部署**: 使用 SDK 的推理 API 部署模型端点
8. **推理验证**: 测试推理端点并监控性能指标

### GitOps 工作流

- 应用配置存储在 Git 仓库中
- 使用 EKS 托管 ArgoCD 进行声明式自动化部署
- 基于 Pull Request 的变更管理,需要审核
- 自动化同步状态监控和漂移告警
- 使用 Kustomize 或 Helm values 的环境特定覆盖

### 部署策略

- 代码和模型流水线的持续集成
- 带环境晋升关卡的分阶段部署(开发 → 测试 → 生产)
- 高风险推理端点变更的金丝雀部署
- 平台组件升级的蓝绿部署
- 失败部署的自动回滚能力
- 带告警的部署指标和健康监控

### 代码审查要求

- 所有 Kubernetes manifests MUST 经过审查
- 资源配额变更 MUST 由管理员批准
- 安全相关配置变更 MUST 经过安全评审
- **SDK 使用验证**: MUST 检查是否优先使用 `sagemaker-hyperpod` SDK 而非自行实现
- **UI 组件验证**: MUST 检查是否使用 Cloudscape 组件,禁止自定义实现或使用其他组件库

### 测试要求

**单元测试**:
- 所有新增业务逻辑 MUST 包含单元测试
- 单元测试 MUST 独立运行,不依赖外部服务
- 目标覆盖率: 后端业务逻辑 ≥70%, 前端组件 ≥60%
- 单元测试 MUST 在 PR 提交时自动运行
- 测试框架: Python (pytest), TypeScript (Jest/Vitest)

**集成测试**:
- 所有 API 端点 MUST 包含集成测试
- 集成测试 MUST 验证数据库交互和服务协作
- 集成测试 MUST 使用测试数据库或容器化环境
- 目标覆盖率: 所有 REST API 端点 100%
- 测试框架: Python (pytest + TestClient), TypeScript (supertest)

**端到端测试 (E2E)**:
- 每个 User Story MUST 至少包含1个完整的端到端测试
- E2E 测试 MUST 验证关键用户旅程的完整性
- E2E 测试 SHOULD 在预发布环境自动执行
- 测试框架: Playwright (前端), pytest (后端工作流)

**性能测试**:
- 关键 API 端点 MUST 包含性能基准测试
- 训练任务提交和监控 MUST 满足响应时间要求 (API P99 <3秒)
- 并发用户场景 MUST 验证系统可扩展性 (1000+ 并发用户)
- 测试框架: Locust (负载测试), K6 (压力测试)

**质量门禁**:
- 代码覆盖率低于目标值的 PR MUST NOT 合并
- 任何测试失败的 PR MUST NOT 合并
- 破坏现有测试的代码变更 MUST NOT 部署
- CI/CD 流水线 MUST 在每次提交时运行全部测试套件

**测试环境**:
- 开发环境: 用于快速迭代和调试
- 集成环境: 用于集成测试和 API 测试
- 预发布环境: 用于 E2E 测试和性能测试
- 生产环境: 仅部署通过所有测试的代码

## Governance

### 宪章效力

本宪章是项目的最高指导文件,所有技术决策和实现 MUST 遵循此宪章中定义的原则。
任何偏离这些原则的行为 MUST 在实施前记录、说明并获得平台治理委员会的批准。

### 平台治理委员会

- 负责审批偏离宪章原则的技术决策
- 负责审批非原生组件的使用申请
- 负责审批绕过 SDK 直接使用底层 API 的申请
- 依赖 Kubernetes Pod Security Admission (PSA) 和 HyperPod Task Governance 进行策略执行
- 新功能 MUST 在开发开始前通过宪法检查关卡

### 修订流程

1. 通过 Pull Request 向宪法文件提出修订
2. 获得平台治理委员会的审核
3. 记录对现有系统的影响评估
4. 获得关键利益相关方的共识
5. 按照语义版本规则更新版本
6. 向所有平台用户传达变更
7. 为任何受影响的组件创建迁移计划

### 版本控制

- MAJOR 版本: 原则移除或根本性重定义
- MINOR 版本: 新增原则或重大扩展
- PATCH 版本: 措辞修订、澄清、格式优化

### 审查周期

治理委员会 MUST 每季度审查此宪章,以确保与企业需求和技术进步保持一致。
主要 AWS 服务更新(HyperPod 功能、EKS 版本、新 Operator 发布、SDK 重大更新)MUST 触发宪章审查。

### 合规检查

- 所有 PR/代码审查 MUST 验证符合本宪章原则
- 架构决策 MUST 证明遵守平台标准
- 复杂性增加 MUST 提供正当理由
- 偏离原则的决策 MUST 记录并获得批准
- 技术选型 MUST 优先验证 HyperPod 原生支持
- 代码实现 MUST 优先验证 `sagemaker-hyperpod` SDK 支持
- UI 实现 MUST 验证使用 Cloudscape 组件,禁止自定义实现

**Version**: 1.7.6 | **Ratified**: 2025-12-23 | **Last Amended**: 2026-01-03
