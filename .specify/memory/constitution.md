<!--
===============================================================================
SYNC IMPACT REPORT
===============================================================================
Version change: 1.5.0 → 1.6.0 (Current)
Version bump rationale: MINOR - 新增 Principle XIII "UI/UX 一致性",建立与 AWS Console 一致的用户界面设计标准

Added principles:
  - XIII. UI/UX Consistency (UI/UX 一致性)
    * **AWS Console 设计对齐**: 遵循 AWS Console 设计语言、交互模式和视觉规范
    * **Cloudscape 组件库**: 强制使用 AWS Cloudscape Design System 作为UI组件库
    * **视觉一致性**: 颜色、字体、图标、间距与 AWS Console 保持统一
    * **交互一致性**: 操作模式、反馈机制、导航模式遵循 AWS 标准
    * **术语一致性**: 使用 AWS 官方术语体系和命名规范
    * **响应式设计**: 支持多种屏幕尺寸,保持一致的信息架构
    * **无障碍访问**: 遵循 WCAG 2.1 AA 级别标准

Added sections:
  - "AWS Console 设计对齐" 核心要求
  - "视觉一致性" 4条具体规范
  - "交互一致性" 4条行为规范
  - "术语一致性" 3条命名规范
  - "实施要求" 5条强制规则
  - "无障碍访问" WCAG 2.1 AA标准

Templates requiring updates:
  ✅ .specify/templates/plan-template.md - 已更新:Constitution Check 添加 Principle XIII 检查项
  ✅ .specify/templates/spec-template.md - 已更新:Technical Constraints 添加 UI/UX 一致性标准
  ⚠ .specify/templates/tasks-template.md - 建议在 Phase 2 添加 Cloudscape 配置任务

Follow-up TODOs:
  - 安装并配置 @cloudscape-design/components 和 @cloudscape-design/global-styles
  - 建立 Cloudscape 组件使用指南,包含常用组件示例
  - 创建 AWS 术语词典,确保全平台用词统一
  - 配置 Storybook 展示 Cloudscape 组件库
  - 进行 WCAG 2.1 AA 级别无障碍访问审计
  - 团队培训:AWS Console 设计规范、Cloudscape 组件库使用、无障碍开发实践
===============================================================================
-->

# AI Studio Platform Constitution

企业级 AI 平台 - 统一模型开发、训练、部署平台

## 愿景声明

构建一个统一的企业级 AI 平台,赋能各业务部门自助式模型开发、训练和部署能力。
平台以 **AWS SageMaker HyperPod 结合 Amazon EKS** 作为核心基础设施,提供可扩展、
高性价比、企业就绪的 AI/ML 运营能力,全面提升企业 AI 模型开发上线效率。

## Core Principles

### I. HyperPod Native-First (原生能力优先)

所有平台功能 MUST 优先采用 AWS SageMaker HyperPod with EKS 提供的原生组件和能力:

- **SDK 交互**: MUST 使用 `sagemaker-hyperpod` Python SDK 作为主要交互接口
- **训练编排**: MUST 使用 HyperPod Training Operator 进行分布式训练任务管理
- **推理部署**: MUST 使用 HyperPod Inference Operator 进行模型服务部署
- **资源治理**: MUST 使用 HyperPod Task Governance 进行配额管理和任务调度
- **可观测性**: MUST 使用 HyperPod Observability Add-on 集成 Prometheus/Grafana
- **开发环境**: MUST 使用 Amazon SageMaker Spaces Add-on 提供 JupyterLab/VS Code IDE
- **弹性训练**: MUST 使用 HyperPod Elastic Agent 支持弹性训练和无检查点训练

**理由**: 原生组件与 HyperPod 基础设施深度集成,提供最佳的弹性恢复、自动扩缩和故障处理能力;
减少自定义开发和维护成本;确保与 AWS 服务更新保持同步。使用官方 SDK 可避免重复造轮子,
降低维护负担,并享受 AWS 提供的持续更新和技术支持。

### II. HyperPod-Enhanced Capabilities First (HyperPod 增强能力优先)

平台 MUST 优先使用 AWS SageMaker HyperPod with EKS 提供的扩展组件和增强能力:

**HyperPod 扩展能力优先**:
- MUST 优先采用 HyperPod 提供的托管组件和扩展能力,而不是重复造轮子
- HyperPod 在 Kubernetes 基础上提供了更多企业级 AI/ML 功能和深度优化
- HyperPod Training/Inference Operators 提供了超越标准 K8S 的弹性训练和自动恢复能力
- HyperPod Task Governance 提供了 AI 工作负载特定的资源调度和配额管理
- HyperPod Observability 集成了 AI/ML 专用的监控指标 (GPU 利用率、训练进度等)
- SageMaker Spaces Add-on 提供了托管的 JupyterLab/VS Code 开发环境

**技术架构约束**:
- 采用 Amazon EKS 作为编排层 (HyperPod 基于 EKS 构建)
- 平台设计以 HyperPod 扩展能力为核心,不要求与开源 K8S 生态完全兼容
- 工作负载 MAY 使用 HyperPod 特有的扩展功能 (如 Checkpointless Training, Elastic Agent)
- 不要求工作负载必须可在标准 K8S 集群上运行
- 允许使用 kubectl、Helm 等 K8S 工具进行管理 (但主要通过 HyperPod SDK 和控制台)

**组件选择原则**:
1. **首选**: HyperPod 托管组件和扩展能力
2. **次选**: 开源 K8S 组件 (仅在 HyperPod 不提供对应功能时)
3. **避免**: 自行实现 HyperPod 已提供的功能

**理由**: AWS SageMaker HyperPod with EKS 是专为企业级 AI/ML 工作负载优化的托管服务,
提供了超越标准 Kubernetes 的弹性恢复、自动扩缩、GPU 优化和 ML 专用功能。优先使用
HyperPod 扩展能力可避免重复造轮子,获得 AWS 深度优化、自动更新和企业支持,显著降低
开发和维护成本。平台聚焦于利用 HyperPod 的独特价值,而不是追求开源 K8S 的通用兼容性。

### III. Multi-Tenant Resource Governance (多租户资源治理)

平台 MUST 支持企业级多租户资源隔离和治理:

- MUST 通过 HyperPod Task Governance 为不同业务部门/项目设置计算配额
- MUST 支持基于优先级的任务调度 (使用 Kueue 进行队列管理)
- MUST 实现细粒度的 GPU/vCPU/内存配额分配
- MUST 提供资源使用报告和成本归属能力
- SHOULD 支持配额借用和空闲资源共享策略

**理由**: 企业 AI 平台需服务多个业务部门,必须确保资源公平分配、成本可追溯、
高优先级任务得到保障。

### IV. Full Lifecycle Observability (全生命周期可观测)

平台 MUST 提供从开发到生产的全链路可观测能力:

- 集群级监控: GPU 利用率、节点健康、网络性能 (NVIDIA DCGM, EFA metrics)
- 任务级监控: 训练进度、队列状态、资源消耗
- 推理级监控: 延迟、吞吐、错误率、Token 级指标
- 实验管理: 集成 MLflow 进行实验追踪和模型管理
- 统一仪表板: 通过 Amazon Managed Grafana 提供可视化

**理由**: 大规模 AI 开发需要深入的可观测性来诊断问题、优化性能、控制成本。

### V. Resilience and Auto-Recovery (弹性与自动恢复)

平台 MUST 充分利用 HyperPod 的弹性基础设施能力:

- 启用深度健康检查 (Deep Health Checks) 检测 GPU 和网络问题
- 启用自动节点恢复 (Automatic Node Recovery) 处理硬件故障
- 支持训练任务自动恢复 (Job Auto-Resume) 使用 Checkpointing
- SHOULD 采用 Checkpointless Training 或 Elastic Training 减少恢复时间
- MUST 配置分层检查点存储 (Tiered Checkpointing) 优化检查点性能

**理由**: 大规模 AI 训练任务运行时间长,硬件故障不可避免;自动恢复能力可将训练
goodput 提升至 95% 以上,显著降低资源浪费。

### VI. Security and Compliance (安全与合规)

平台 MUST 满足企业级安全要求:

- 外部入口和 API 通信 MUST 使用 TLS 1.2+ 加密;集群内部通信依赖 VPC 网络隔离和 Nitro 硬件级加密保护
- 支持 VPC 隔离和私有端点访问
- 集成 IAM 和 Kubernetes RBAC 进行细粒度权限控制
- 支持使用客户管理的 KMS 密钥进行数据加密
- MUST 记录所有安全相关事件和访问日志
- SHOULD 支持合规审计和资源标签策略

**理由**: 企业 AI 平台处理敏感数据和模型,必须满足数据安全、访问控制和审计追溯的要求。

### VII. Platform First (平台优先)

企业 AI 平台 MUST 作为统一、内聚的平台构建,而非零散工具的集合:

- 所有功能 MUST 集成到具有共享标准的通用架构中
- 每个组件 MUST 支持更广泛的平台能力,而非孤立运行
- 平台 MUST 维护集中治理、标准和基础设施

**理由**: 碎片化的工具集会造成运维开销、不一致的用户体验和维护负担,
从而削弱企业采用率。

### VIII. Model Lifecycle Management (模型生命周期管理)

所有模型 MUST 遵循从开发到部署到监控的标准化生命周期:

- 模型的版本控制、追踪和可审计性不可协商
- 每个模型 MUST 保持训练数据、代码、参数和部署目标之间的清晰血缘关系
- 使用 SageMaker Model Registry 进行模型版本控制和审批工作流
- MLflow 集成用于实验追踪
- 生产部署前的自动化模型验证关卡
- 明确的制品存储和保留策略

**理由**: 标准化的模型生命周期管理确保模型质量、可追溯性和合规性。

### IX. Infrastructure as Code Excellence (基础设施即代码卓越)

所有基础设施 MUST 通过基础设施即代码 (IaC) 实践进行定义、版本控制和部署:

- 禁止在生产环境中进行手动基础设施变更
- 基础设施代码 MUST 与应用代码接受同等严格的审查
- 使用 AWS CDK 进行基础设施配置(TypeScript 或 Python)
- 使用 EKS 托管 ArgoCD 的 GitOps 工作流进行集群配置
- 使用 Helm charts 进行应用部署标准化
- 版本控制的集群蓝图和附加组件配置
- 自动化漂移检测和修复

**理由**: IaC 确保基础设施的一致性、可重复性和可审计性,减少人为错误和配置漂移。

### X. Test Quality Assurance (测试质量保证)

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

### XI. SDK-First Development (SDK 优先开发)

所有与 SageMaker HyperPod 交互的功能实现 MUST 优先使用官方 `sagemaker-hyperpod` Python SDK:

**强制使用 SDK 的场景**:
- **集群管理**: MUST 使用 SDK 的集群连接、配置和管理功能
  - 集群连接和切换
  - 集群信息查询和监控
  - 集群配置更新
- **训练任务管理**: MUST 使用 SDK 的训练 API 提交和管理分布式训练任务
  - 训练任务提交 (PyTorch, TensorFlow, MPI 等)
  - 训练状态监控和日志获取
  - 训练任务生命周期管理 (启动、停止、重启)
  - 分布式训练配置 (节点数、GPU配置、容错策略)
- **推理部署**: MUST 使用 SDK 的推理 API 部署和管理模型端点
  - 模型端点创建和配置
  - 推理服务扩缩容
  - 端点健康检查和监控
- **开发空间**: MUST 使用 SDK 的 Spaces API 管理 JupyterLab/VS Code 开发环境
  - Spaces 创建和配置
  - 开发环境生命周期管理
  - 资源配额分配

**仅在以下情况可使用底层 Kubernetes API**:
- SDK 明确不支持的高级定制需求
- 需要直接操作 Kubernetes 资源进行调试或故障排查
- SDK 功能无法满足特定性能或功能要求,且已在架构评审中获批

**实施要求**:
- 开发新功能前 MUST 首先查阅 `sagemaker-hyperpod` SDK 文档
- 代码审查 MUST 验证是否优先使用 SDK 而非自行实现
- 如需绕过 SDK 直接使用 K8S API,MUST 在代码中明确注释说明原因
- 平台 API 设计 MUST 与 SDK 保持一致的抽象层级和术语

**理由**:
1. **避免重复造轮子**: SDK 已封装 HyperPod 最佳实践,无需自行实现
2. **降低维护成本**: AWS 负责 SDK 维护和更新,平台无需跟进底层 API 变化
3. **保证兼容性**: SDK 与 HyperPod 服务版本同步更新,确保功能兼容性
4. **获得技术支持**: 使用官方 SDK 可获得 AWS 技术支持和社区帮助
5. **提升开发效率**: SDK 提供高层抽象,简化开发流程,减少样板代码

**参考文档**: https://sagemaker-hyperpod-cli.readthedocs.io/en/latest/

### XII. Code Quality and Design Excellence (代码质量与设计卓越)

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
- **MUST 优先使用 HyperPod SDK** 而非自行实现 (如 Principle XI 所述)
- **MUST 优先使用官方推荐的库**: FastAPI、SQLAlchemy、Pydantic、pytest (Python)
- **MUST 优先使用生态成熟的组件**: React、TypeScript、Zustand、TanStack Query (前端)
- **仅在以下情况自行实现**:
  - 现有库明确不支持业务需求
  - 现有库存在严重性能或安全问题
  - 轻量级工具函数 (<50行代码)

**代码审查标准**:
- 所有代码 MUST 通过代码审查才能合并
- 审查必须验证: SOLID 原则遵循、代码整洁度、组件复用合理性
- 复杂逻辑 MUST 包含单元测试 (覆盖率要求见 Principle X)
- 新增依赖 MUST 在 PR 中说明理由和评估替代方案

**技术债务管理**:
- 发现技术债务 MUST 记录在 TODO 或 Issue 中
- 严重技术债务 (影响性能、安全、可维护性) MUST 优先修复
- 不允许为了短期交付而故意引入技术债务

**理由**: 代码质量直接影响系统的长期可维护性、演进能力和团队生产力。遵循软件工程
最佳实践和代码整洁之道,可以减少bug、降低维护成本、提升开发效率。优先使用成熟的
SDK和组件可以避免重复造轮子,利用社区智慧,获得持续更新和技术支持,显著降低开发
和维护负担。

### XIII. UI/UX Consistency (UI/UX 一致性)

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

- **Kubeflow Training Operator**: PyTorchJob、TFJob 等 Kubernetes 原生训练

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

**必装 EKS Add-ons 和 Operators**:
- HyperPod Training Operator(分布式训练管理)
- HyperPod Inference Operator(模型推理部署)
- HyperPod Task Governance(资源配额和调度)
- HyperPod Observability Add-on(监控和可观测性)
- HyperPod Elastic Agent(弹性训练支持)
- Amazon SageMaker Spaces Add-on(IDE 和 Notebooks 开发环境)
- cert-manager(证书管理,Training Operator 前置依赖)
- EKS Pod Identity Agent(安全凭证管理)

**集群运维要求**:
- 使用最新 HyperPod AMI 版本(通过 UpdateClusterSoftware API 升级)
- 启用健康监控和自动实例替换
- 可复现环境的集群配置模板
- 支持多节点分布式训练模式
- 支持弹性训练(Elastic Training)和无检查点训练(Checkpointless Training)

### 禁止事项

- MUST NOT 使用 Slurm 编排 (本项目选择 EKS 路线)
- MUST NOT 绕过 Task Governance 直接提交无配额管理的作业
- MUST NOT 在生产环境禁用健康检查或自动恢复功能
- MUST NOT 使用非加密的通信通道
- MUST NOT 在 SDK 提供相同功能的情况下自行实现底层 K8S 交互
- **MUST NOT 使用 Cloudscape 以外的 UI 组件库** (如 MUI, Ant Design, Element Plus)
- **MUST NOT 自行实现 Cloudscape 已提供的 UI 组件**

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

**Version**: 1.6.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2026-01-02
