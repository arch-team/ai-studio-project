# 企业级AI训练平台 - 实施任务清单

## 概述

本文档包含企业级AI训练平台的完整实施任务清单,共计 159 个任务,按用户故事和优先级组织。

**技术栈**:
- 后端: Python 3.11, FastAPI 0.109+, SQLAlchemy 2.0+, Alembic, sagemaker-hyperpod SDK (包含 Space 模块), boto3 (AWS SDK for S3/CloudWatch/IAM 等非 HyperPod 服务)
- 前端: React 18, TypeScript 5.3+, AWS Cloudscape Design System, Vite, Zustand, TanStack Query v5
- 数据库: MySQL 8.0.28 (开发), Aurora MySQL 3.04.x (生产)
- 存储: FSx for Lustre (训练数据), S3 (模型/检查点)
- 监控: HyperPod Observability Add-on (Prometheus + Grafana)
- 在线开发环境: Amazon SageMaker Spaces Add-on (JupyterLab/VS Code IDE)

**用户故事优先级**:
- **P1 (Must-Have)**: US1 训练任务管理, US2 数据集管理, US3 资源配额和集群监控
- **P2 (Important)**: US4 资源使用报表和成本分析, US5 在线开发环境

**MVP 范围**: Phase 0 (SDK 可行性研究) + Phase 1 (Setup + IaC) + Phase 2 (Foundational) + Phase 3 (US1) + Phase 4 (US2) + Phase 5 (US3) = 105 个任务,提供完整的 P1 核心功能集:HyperPod SDK 方法验证（Phase 0 研究阶段完成）及备选方案、项目基础结构、IaC 基础、HyperPod EKS 集群（拆分为基础配置/节点组/安全配置 3 个子任务）、HyperPod Add-ons (Training Operator/Kueue/Observability/Elastic Agent/Spaces)、FSx for Lustre 高性能存储、ALB 和 TLS 终止配置、基础设施验证测试、企业级认证、数据加密、训练任务管理、模型版本控制、数据集管理、资源配额、集群监控和审计日志。

---

## Phase 0: 技术可行性研究 (2 tasks)

**目标**: 验证 HyperPod SDK 可用性,确保后续开发基于真实可用的 API,避免架构假设错误

**关键产物**: SDK 方法签名参考文档、功能缺口分析、备选方案设计(如需)

### HyperPod SDK 方法验证
- [X] [T000] [P] HyperPod SDK 方法名验证 - 查阅 `sagemaker-hyperpod` SDK 官方文档,验证并记录正确的方法签名和参数：
  - **Training 模块**: 训练任务提交、状态查询、暂停/恢复/终止方法的准确方法名和签名
    - **状态信息完整性验证**: 验证 `get_training_job_status()` 返回值是否包含所有必需状态（Submitted/Running/Paused/Preempted/Completed/Failed）和状态转换所需的详细信息（抢占原因、失败分类、检查点路径等）。如状态信息不足以支持 spec.md Training Job State Model 的完整状态转换逻辑，记录缺口到 `docs/hyperpod-sdk-gaps.md` 并触发 T000-fallback
  - **Space 模块**: Space 创建、删除、查询方法的准确方法名和签名
  - **Cluster 模块**: 集群状态查询、节点列表方法的准确方法名和签名
  - **输出产物**:
    - `docs/hyperpod-sdk-reference.md`: SDK 方法签名参考文档,包含示例代码和参数说明
    - `docs/hyperpod-sdk-capability-matrix.md`: SDK 能力矩阵（填充 plan.md 中定义的功能-工具矩阵，每个功能注明最佳实现工具和选型依据）
    - `docs/technical-decision-guideline.md`: 技术选型决策指南（开发时查阅的 SDK/boto3/CLI/kubectl 选型标准和最佳实践）
    - `docs/hyperpod-sdk-gaps.md`: SDK 功能缺口分析(如有缺口,列出需要降级使用 boto3/CLI/kubectl 的场景)
  - **风险评估**: 如发现 SDK 方法不可用或签名不符,立即触发 T000-fallback 任务
    - **触发条件说明**:
      - "方法不存在": 核心方法（create/get/pause/resume/terminate）在 SDK 中找不到
      - "签名不符": 参数名称/类型/数量与预期不匹配，或返回值格式严重不符
      - "功能不完整": 核心方法存在但不支持必需特性（如从检查点恢复、Gang Scheduling 配置）
    - **触发原因记录**: T000 执行者应详细记录触发原因、影响范围和备选方案建议到 `docs/hyperpod-sdk-gaps.md`
  - **参考**: [SageMaker HyperPod SDK Documentation](https://sagemaker-hyperpod-cli.readthedocs.io/)
  - **工作量估算**: 0.5 人日
- [X] [T000-fallback] HyperPod SDK 备选方案设计与 POC 验证 (条件任务,仅在 T000 发现 SDK 不可用时执行) - 设计并验证 boto3/kubernetes-client 备选方案:
  - **触发条件**: T000 验证发现 SDK 方法不存在、签名不符或功能不完整
  - **阶段 1: 备选方案分析** (0.5 人日)
    - 评估 boto3 (SageMaker API) 的可行性: 支持的训练任务管理 API、限制和约束
    - 评估 kubernetes-client (直接操作 CRD) 的可行性: PyTorchJob/TFJob CRD 操作、Kueue Workload 查询
    - 接口设计: 设计统一的客户端抽象层 (`clients/training_client.py`),支持 SDK/boto3/kubernetes-client 多种后端
  - **阶段 2: POC 技术验证** (1 人日)
    - **boto3 POC 验证** (验证集群管理功能):
      - 查询 HyperPod 集群状态: `describe_cluster(ClusterName=...)`
      - 列出集群节点: `list_cluster_nodes(ClusterName=...)`
      - 验证集群级别的监控指标获取
      - 明确结论: boto3 仅用于集群管理，不适用于训练任务管理
    - **kubernetes-client POC 验证**:
      - 使用 kubernetes-client 查询 PyTorchJob CRD 状态
      - 查询 Kueue Workload 状态和优先级
      - 创建 NetworkPolicy 资源
      - 验证错误处理和重试机制的实现复杂度
    - **性能和兼容性测试**:
      - 评估备选方案的 API 响应时间
      - 验证与 HyperPod Training Operator 的兼容性
      - 识别潜在的竞态条件和边界情况
  - **阶段 3: 方案整合与治理** (0.5 人日)
    - 基于 POC 结果完善接口设计
    - 准备平台治理委员会例外申请文档 (遵循宪章 Principle I.B)
    - 评估对 Phase 2/3/7 任务的影响范围和返工成本
    - **风险缓解**: 如阶段 1 评估发现 boto3 和 kubernetes-client 两种备选方案都不可行，应立即上报治理委员会并停止 POC，避免无效工作
  - **输出产物**:
    - `docs/hyperpod-sdk-fallback.md`: 备选方案详细设计 (含 POC 验证结果)
    - `docs/exception-request-template.md`: 例外申请模板
    - `docs/adr/001-sdk-fallback-strategy.md`: 架构决策记录
    - `poc/boto3-training-poc.py`: boto3 训练任务管理 POC 代码
    - `poc/k8s-client-poc.py`: kubernetes-client CRD 操作 POC 代码
    - `docs/poc-validation-report.md`: POC 验证报告 (包含性能测试结果和风险评估)
  - **依赖**: T000 (SDK 方法验证结果)
  - **工作量估算**: 2 人日

**Phase 0 完成标准**:
- ✅ `docs/hyperpod-sdk-reference.md` 文档完成,包含所有核心方法签名
- ✅ SDK 可用性决策明确: 完全可用 / 部分可用(需备选方案) / 不可用(需例外审批)
- ✅ 如需备选方案,`docs/hyperpod-sdk-fallback.md` 设计完成
- ✅ 治理委员会审批通过 (如需例外)

**Phase 0 → Phase 1 交接**:
- SDK 可用性结论和验证报告
- 方法签名参考文档供 Phase 1 IaC 和后端开发使用
- 备选方案设计 (如适用)
- 风险和约束条件清单

---

## Phase 1: Setup - 项目初始化和基础设施即代码 (18 tasks)

**目标**: 搭建项目基础结构,配置开发环境,建立 IaC 基础

**前置条件**: Phase 0 SDK 验证完成,方法签名参考文档可用

### 后端项目结构
- [X] [T001] [P] 创建 backend/ 项目结构 - 使用 FastAPI + SQLAlchemy 2.0 异步架构,采用 Clean Architecture 四层架构,创建 `backend/src/` 目录结构 (domain/, application/, infrastructure/, api/, core/)
- [X] [T004] [P] 配置 backend/requirements.txt - 添加 fastapi==0.109.0, sqlalchemy==2.0+, alembic, aiomysql, pydantic==2.0+, boto3, sagemaker-hyperpod SDK

### 前端项目结构
- [X] [T002] [P] 创建 frontend/ 项目结构 - 使用 Vite + React 18 + TypeScript,创建 `frontend/src/` 目录结构 (pages/, components/, layouts/, store/, lib/)
- [X] [T005] [P] 配置 frontend/package.json - 添加 react@18, @cloudscape-design/components, zustand, @tanstack/react-query@5, react-router-dom

### 开发环境配置
- [X] [T003] 创建 Docker Compose 配置 - MySQL 8.0.28 服务,端口 3306,环境变量配置 (`docker-compose.yml`)
- [X] [T006] 创建环境变量模板 - `.env.example` 包含 DATABASE_URL, AWS_REGION, HYPERPOD_CLUSTER_ARN 等必需配置
  - **AWS 凭证配置**: 支持 AWS CLI profile 或环境变量 (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)
  - **开发者 IAM 权限**: 需要 SageMaker、EKS、S3、CloudWatch 相关权限 (具体策略在 IaC 中定义)
  - **kubectl 配置**: 通过 `aws eks update-kubeconfig --name <cluster-name> --region <region>` 配置集群访问

### 数据库迁移系统
- [X] [T007] [P] 初始化 Alembic 迁移系统 - 配置 `backend/alembic.ini` 和 `backend/alembic/env.py`,支持 SQLAlchemy 2.0 异步引擎

### 项目文档
- [X] [T008] 初始化项目文档 - 创建 `README.md` (项目概述,快速启动), `CONTRIBUTING.md` (开发规范,提交流程)

### 基础设施即代码 (IaC)
- [X] [T008a] AWS CDK 项目结构 - 创建 `infrastructure/cdk/` 目录结构,初始化 CDK Python 项目 (与后端技术栈一致),配置 `cdk.json` 和 `requirements.txt`,定义 Stack 组织结构 (NetworkStack, DatabaseStack, StorageStack, ComputeStack),配置多环境支持 (dev/staging/prod)
  - **CDK Bootstrap 配置** (状态管理基础):
    - 执行 `cdk bootstrap aws://{account}/{region}` 初始化 CDKToolkit Stack
    - **多环境 Bootstrap**: 为 dev/staging/prod 账户分别执行 Bootstrap,使用统一的 qualifier (默认 `hnb659fds`)
    - **Bootstrap 存储桶验证**: 确认 `cdk-{qualifier}-assets-{account}-{region}` 存储桶已创建
    - **默认安全配置**: 验证 Bootstrap 存储桶已启用 SSE-S3 加密和版本控制 (CDK 默认行为)
    - **访问控制**: Bootstrap 角色仅允许 CDK 部署流程访问,禁止直接人工操作
    - **ECR 仓库**: 验证 `cdk-{qualifier}-container-assets-{account}-{region}` ECR 仓库已创建 (用于 Docker 镜像资产)
    - **Bootstrap 版本管理**: 记录 Bootstrap 版本号 (`cdk bootstrap --show-template` 获取),升级 CDK 时同步升级 Bootstrap
    - **验证脚本**: 创建 `infrastructure/scripts/verify-bootstrap.sh` 验证 Bootstrap 状态完整性
  - **并发部署控制** (状态锁定机制):
    - **锁定机制**: 依赖 CloudFormation 原生 Stack 操作锁定 (IN_PROGRESS 状态阻止并发操作)
    - **锁定冲突处理**: 遇到 "Stack is in UPDATE_IN_PROGRESS state" 错误时,等待当前操作完成后重试 (建议等待间隔 30 秒)
    - **死锁恢复流程**: Stack 卡在 `*_IN_PROGRESS` 状态超过 1 小时,通过 AWS Console 取消 Stack 操作或联系平台管理员介入
    - **生产环境保护**: 生产环境部署仅允许通过 CI/CD 流水线执行,本地 CLI 禁止直接部署 (`cdk deploy --context env=prod` 需要额外审批凭证)
    - **部署协调**: 团队成员部署前在 Slack/Teams 频道通知,避免同时操作同一 Stack
- [X] [T008b] AWS CDK 核心 Stacks - 编写以下基础设施 Stacks:
  - **VPC Stack**:
    - **VPC CIDR 配置**: 默认 10.0.0.0/16 (65,536 个 IP 地址),支持通过 CDK 上下文变量配置 (例如 `cdk.json` 中的 `vpcCidr` 参数或 `cdk deploy --context vpcCidr=10.0.0.0/15`)
    - **容量验证**: CDK Stack 实现时需验证 CIDR 容量满足集群扩展需求 (计算公式: 可用节点数 ≈ 私有应用层子网IP数 / 每节点平均IP需求20,目标支持 ≥1000 节点)
    - **子网自动划分**: 根据配置的 VPC CIDR 自动计算子网划分 (保持比例: 公有子网18.75%, 私有应用层37.5%, 私有数据层18.75%)
    - **三层隔离设计** (符合 AWS Well-Architected 安全最佳实践):
      - 公有子网 (默认): 10.0.0.0/20, 10.0.16.0/20, 10.0.32.0/20 (3 个 AZ, 用于 NAT Gateway/ALB)
      - 私有子网-应用层 (默认): 10.0.64.0/19, 10.0.96.0/19, 10.0.128.0/19 (3 个 AZ, 用于 EKS 节点/RDS)
      - 私有子网-数据层 (默认): 10.0.160.0/20, 10.0.176.0/20, 10.0.192.0/20 (3 个 AZ, 用于 FSx/ElastiCache)
    - **部署模式配置** (通过 CDK 上下文变量 `deploymentMode` 选择,优化跨AZ流量成本):
      - `single-az`: 单AZ部署 (开发/测试环境,跨AZ流量费用 ~$0/月,但无高可用保障)
      - `multi-az` (默认): 多AZ高可用部署 (生产环境,所有层3个AZ均衡分布)
      - `hybrid`: 混合模式 (推荐用于生产环境,计算层3AZ + 数据层主实例单AZ,跨AZ流量费用减少60-70%)
    - **成本优化策略**:
      - 混合模式: FSx/RDS 主实例固定在 AZ-a,备份在 AZ-b/AZ-c,配合 EKS 节点 AZ 亲和性调度 (参见 T008c-2),减少跨AZ数据传输费用
      - 拓扑感知: EKS 节点组配置 `topologySpreadConstraints` 和 `nodeAffinity`,训练任务 Pod 优先调度到数据层同AZ节点
      - 数据本地化: 利用节点 NVMe 本地存储缓存 FSx 数据,减少重复跨AZ传输
    - NAT Gateway: 在 2 个 AZ 部署 (AZ-a 和 AZ-b, 成本优化同时保留高可用)
      - AZ-a 私有子网 → NAT Gateway-a
      - AZ-b 私有子网 → NAT Gateway-b
      - AZ-c 私有子网 → NAT Gateway-b (跨 AZ 路由)
      - 成本节省: $100/月 → $67/月 (节省 33%)
    - **VPC 端点 (PrivateLink)** - 创建以下必需端点（参考 plan.md L54-64）:
      - S3 Gateway 端点 (无额外费用)
      - ECR Interface 端点 (API + Docker)
      - CloudWatch Interface 端点 (Logs + Monitoring)
      - STS Interface 端点
      - SageMaker API Interface 端点
      - **EFS Interface 端点** (SageMaker Spaces 持久化存储必需，US5 依赖)
      - 配置安全组规则允许 EKS 节点访问所有端点
    - 安全组配置
  - **RDS Aurora MySQL Stack**:
    - Serverless v2 配置: 最小 ACU 0.5 (开发环境可暂停), 最大 ACU 16 (生产环境), 自动扩缩容
    - 备份策略: 自动备份保留期 7 天, 备份窗口 UTC 03:00-04:00, 启用时间点恢复 (PITR)
    - 连接池: 启用 RDS Proxy (连接池大小根据 ACU 自动调整), 空闲连接超时 30 分钟
    - 高可用: 多可用区部署, 故障转移时间 <30 秒
  - **S3 Buckets Stack**: 创建以下存储桶,均启用版本控制和生命周期策略:
    - `{project}-datasets-{env}`: 训练数据集存储
    - `{project}-models-{env}`: 训练产出的模型文件
    - `{project}-checkpoints-{env}`: 检查点和快照文件
    - **静态数据加密配置**: 所有存储桶启用 SSE-KMS 默认加密，统一使用 AWS 托管密钥 (aws/s3)，S3 自动对所有上传对象应用加密,无需客户端指定加密参数。MVP 阶段简化配置，如需更强审计能力可迁移到 CMK
    - **传输加密强制策略**: 配置 Bucket Policy 拒绝非 HTTPS 传输 (aws:SecureTransport = false),确保数据传输安全
    - **验证测试**:
      - ❌ HTTP PUT 请求被拒绝 (403 Forbidden)
      - ✅ HTTPS PUT 请求成功,且对象自动应用 SSE-KMS 加密
      - ✅ 通过 GetObject API 验证对象 ServerSideEncryption=aws:kms
      - ✅ 通过 S3 Console 验证存储桶默认加密配置已启用
  - **IAM Roles Stack**: EKS 节点角色、应用服务角色 (遵循最小权限原则)

### HyperPod EKS 集群创建
- [X] [T008c-1] [P] HyperPod EKS 集群基础配置 - `infrastructure/cdk/stacks/hyperpod_stack.py`,创建 SageMaker HyperPod with EKS 集群基础:
  - **EKS 集群配置**: 版本 EKS 1.32+,配置 VPC 和子网关联 (使用 T008b 创建的 VPC)
  - **EKS Add-ons**: 安装 EBS CSI Driver (≥v1.28.0), FSx CSI Driver (≥v1.9.0), VPC CNI (≥v1.16.0)，详细版本要求参见 plan.md L35-38
  - **输出**: HyperPod 集群 ARN、EKS 集群名称、集群 API Endpoint
  - **依赖**: T008a (CDK 项目结构), T008b (VPC Stack)
  - **参考**: plan.md Constraints "Requires AWS SageMaker HyperPod with EKS infrastructure", spec.md FR-001
- [X] [T008c-2] [P] GPU 节点组和 Auto Scaling 配置 - `infrastructure/cdk/stacks/hyperpod_stack.py`,创建 GPU 节点组和扩缩容策略:
  - **GPU 节点组**: 创建 GPU 节点组 (p4d.24xlarge, p5.48xlarge, trn1.32xlarge),配置 Auto Scaling Group (最小 2 节点,最大 100 节点)
  - **Auto Scaling 策略**（使用 SageMaker HyperPod Autoscaling 原生能力）:
    - 扩容触发: Kueue 队列中 Pending Workloads 数量 >0 且持续 5 分钟（HyperPod 默认配置）
    - 缩容触发: 节点 GPU 利用率 <20% 且持续 15 分钟（HyperPod 默认配置）
    - 缩容保护: 运行中训练任务的节点不参与缩容（HyperPod 原生能力）
    - 冷却期: 扩容后 10 分钟内不触发缩容（HyperPod 默认配置）
    - 配置方式: 使用 HyperPod Auto Scaling Group 配置，无定制化扩展
  - **AZ 亲和性调度配置** (成本优化,减少跨AZ流量):
    - 节点标签: 为每个节点自动添加 `topology.kubernetes.io/zone` 标签 (例如 `us-east-1a`)
    - 拓扑约束: 配置节点组 `topologySpreadConstraints`,优先在数据层主 AZ (默认 AZ-a) 部署节点
    - 训练任务亲和性模板: 提供 Pod 模板配置 `nodeAffinity`,自动将训练任务调度到与 FSx/RDS 同 AZ 的节点
    - 数据本地化: 启用节点 NVMe 本地存储作为 FSx 数据缓存层,减少重复跨AZ数据传输
    - 配置示例 (注入到训练任务 Pod):
      ```yaml
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-east-1a  # 与 FSx/RDS 主实例部署的 AZ 一致
      ```
  - **EFA 网络配置**: 启用 EFA (Elastic Fabric Adapter) 高性能网络,配置网络拓扑优化
  - **输出**: 节点组 ID、Auto Scaling 策略配置参数、AZ 亲和性配置、EFA 网络配置
  - **依赖**: T008c-1 (EKS 集群基础配置), T008b (VPC Stack 部署模式配置)
  - **参考**: spec.md FR-003/FR-004
- [X] [T008c-3] [P] IAM 和安全配置 - `infrastructure/cdk/stacks/hyperpod_stack.py`,配置 IAM 角色和安全策略:
  - **IAM 角色配置** (遵循最小权限原则):
    - **EKS 节点角色**: ec2:DescribeInstances, ec2:DescribeNetworkInterfaces, ecr:GetAuthorizationToken, ecr:BatchGetImage, ecr:GetDownloadUrlForLayer, s3:GetObject/PutObject (限定 datasets/models/checkpoints bucket), logs:CreateLogStream/PutLogEvents, sts:AssumeRole
    - **训练任务 Pod IAM 角色**: s3:GetObject/PutObject (限定训练相关 bucket), sagemaker:Describe*/List* (只读), cloudwatch:PutMetricData, logs:CreateLogStream/PutLogEvents
    - **监控 Pod IAM 角色**: cloudwatch:GetMetricData/PutMetricData, logs:DescribeLogStreams/GetLogEvents (只读)
    - **Service Account 映射**: training-sa → Training Pod Role, monitoring-sa → Monitoring Role, spaces-sa → Spaces Role
  - **RBAC 策略配置**:
    - **ClusterRole**: hyperpod-admin (集群管理), hyperpod-project-manager (项目管理 + 资源配额), hyperpod-engineer (训练任务 CRUD), hyperpod-viewer (只读)
    - **Role (命名空间级)**: training-job-manager (训练任务 CRUD + Pod 日志查看), config-reader (ConfigMap/Secret 只读)
    - **RoleBinding**: 用户角色映射到对应的 ClusterRole/Role (admin → hyperpod-admin, project_manager → hyperpod-project-manager, engineer → hyperpod-engineer, viewer → hyperpod-viewer)
  - **安全配置**: 配置 Security Group (训练任务端口、Kubernetes API 端口、EFA 网络端口),启用 Pod Security Standards (restricted 模式)
  - **高可用性配置**: 多可用区部署 (至少 3 个 AZ),控制平面冗余
  - **输出**: IAM 角色 ARN、Security Group ID、RBAC 策略清单、权限验证报告
  - **依赖**: T008c-1 (EKS 集群基础配置)
  - **参考**: spec.md FR-001 (安全要求), AWS EKS IAM 最佳实践, K8s RBAC 文档

### HyperPod Add-ons 安装

**CDK 与 K8s 清单职责边界** (遵循 AWS 最佳实践):
| 资源类型 | 管理方式 | 存放位置 |
|---------|---------|---------|
| AWS 原生资源 (VPC/RDS/S3/FSx) | CDK Stack | `infrastructure/cdk/stacks/` |
| EKS 集群 | CDK Stack | `infrastructure/cdk/stacks/` |
| AWS 托管 EKS Add-ons (含 HyperPod 全系列) | CDK `eks.Addon` | `infrastructure/cdk/stacks/hyperpod_addons_stack.py` |
| K8s 原生资源 (NetworkPolicy/RBAC/PriorityClass) | K8s 清单 | `infrastructure/k8s/` |
| ArgoCD Application | K8s 清单 | `infrastructure/argocd/` |

- [X] [T008d-1] [P] 训练核心组件安装 - `infrastructure/cdk/stacks/hyperpod_addons_stack.py`,使用 CDK `eks.Addon` 安装训练调度核心组件 (已完成: CDK Stack + 验证脚本):
  - **Training Operator** (Add-on: `amazon-sagemaker-hyperpod-training-operator`): 安装 HyperPod Training Operator (PyTorchJob, TensorFlowJob CRD),配置训练框架支持 (PyTorch DDP/FSDP/DeepSpeed ZeRO),验证 Webhook 就绪
  - **Task Governance** (Add-on: `amazon-sagemaker-hyperpod-taskgovernance`): 安装 HyperPod Task Governance (基于 Kueue),自动创建 ClusterQueue 和 LocalQueue,配置 Gang Scheduling (默认 60 秒超时)
  - **PriorityClass 配置**: 由 Task Governance Add-on 自动提供,三级优先级配置 (training-priority-low: 100, training-priority-medium: 500, training-priority-high: 1000) 遵循 spec.md FR-004 优先级数值映射
  - **抢占策略**: 完全遵循 Kueue 原生抢占行为,不做自定义扩展。具体参数 (冷却期、借用策略等) 以 HyperPod Task Governance 默认配置为准,参见 [Kueue Preemption Documentation](https://kueue.sigs.k8s.io/docs/concepts/preemption/)
  - **验证测试**: 提交测试 PyTorchJob (single-node hello-world),验证 Job 状态转换为 Succeeded,验证 Kueue Workload 调度生效,验证 Training Operator Webhook 响应 (curl localhost:9443/healthz)
  - **依赖**: T008c-1, T008c-2, T008c-3 (HyperPod EKS 集群完整配置)
  - **参考**: spec.md FR-001 (Training Operator), FR-004 (Kueue), [HyperPod Training Operator 安装文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html)
- [X] [T008d-2] [P] 监控组件安装 - `infrastructure/cdk/stacks/hyperpod_addons_stack.py`,使用 CDK `eks.Addon` 安装运维监控组件 (已实现: Observability Add-on):
  - **Observability** (Add-on: `amazon-sagemaker-hyperpod-observability`): 部署 HyperPod Observability (Prometheus + Grafana),自动配置 Node Exporter, cAdvisor, DCGM Exporter (GPU 指标),配置数据保留期 (30 天),创建预定义 Grafana 仪表盘 (集群健康、训练任务分布、资源利用率)
  - **注意: Elastic Agent 不是 EKS Add-on**: HyperPod Elastic Agent (检查点管理、Auto-Resume) 是 Python 包,需要在训练容器镜像中安装 (`pip install hyperpod-elastic-agent`),而非作为 EKS 集群 add-on 部署。详见 [HyperPod Training Operator 安装文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html)
  - **验证测试**: 查询 Prometheus 指标 (up, node_cpu_seconds_total),访问 Grafana 仪表盘
  - **依赖**: T008d-1 (需要 Training Operator CRD 用于监控训练任务)
  - **参考**: spec.md FR-007/FR-016 (Observability), [HyperPod Observability 文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-dashboard.html)
- [X] [T008d-3] [P] 开发环境组件安装 - `infrastructure/cdk/stacks/hyperpod_addons_stack.py`,使用 CDK `eks.Addon` 安装 Spaces Add-on:
  - **Spaces Add-on** (Add-on: `amazon-sagemaker-spaces`): 安装 Amazon SageMaker Spaces Add-on,配置 JupyterLab 和 VS Code IDE 镜像 (Data Science, PyTorch, TensorFlow),配置 EFS 持久化存储挂载,配置自动保存间隔 (JupyterLab 120 秒, VS Code 1 秒)
  - **验证测试**: 验证 Spaces CRD 注册,检查 Spaces Controller Pod 状态,创建测试 Space (可选,建议在 US5 开发时执行)
  - **依赖**: T008c-1, T008c-2, T008c-3 (HyperPod EKS 集群完整配置,与训练组件无依赖,可并行执行)
  - **参考**: spec.md FR-012/SC-015 (Spaces), [SageMaker Spaces Add-on 安装文档](https://docs.aws.amazon.com/sagemaker/latest/dg/operator-install.html)

### FSx for Lustre 文件系统创建
- [X] [T008e] [P] FSx for Lustre Stack - `infrastructure/cdk/stacks/fsx_stack.py`,创建 Amazon FSx for Lustre 高性能文件系统:
  - **文件系统配置**: 创建 FSx for Lustre 文件系统,配置 Persistent_2 部署类型 (持久化存储),默认使用 500 MB/s/TiB 吞吐量级别 (配合 10 TiB 容量可达 5 GB/s，满足 spec.md ≥5GB/s 基线需求)。成本优化策略：500 MB/s/TiB 相比 1000 MB/s/TiB 节省约 50% 成本 (~$6,500/月)，适用于大多数训练场景 (单任务 GPU ≤8)。性能不达标时可通过调优方案升级到 1000 MB/s/TiB (参见性能验证部分)
  - **容量规划**: 根据 spec.md NFR-001 FSx 容量规划公式计算初始容量 (公式: MAX(10 TiB, MAX(dataset_size)×1.5, concurrent_jobs×avg_dataset_size×1.2))。建议初始容量配置:小规模训练 18 TiB、中规模训练 48 TiB、大规模训练 144 TiB。启用自动扩容策略 (使用率 >80% 触发扩容，每次扩容增加当前容量 20%，最小增量 10 TiB),最大容量 160 TiB (AWS FSx 单文件系统限制)
  - **S3 集成**: 配置 S3 Data Repository Association,链接训练数据 S3 存储桶 (T008b 创建),启用自动导入/导出 (ImportPath, ExportPath),配置 AutoImportPolicy (NEW/CHANGED/DELETED 事件自动同步)
  - **网络配置**: 部署到 T008b 创建的 VPC 私有子网,配置安全组 (允许 EKS 节点访问 FSx 端口 988, 1021-1023),启用 VPC 内 DNS 解析
  - **FSx CSI Driver**: 使用 T008c-1 中已安装的 AWS FSx CSI Driver,创建 StorageClass (provisioner: fsx.csi.aws.com, parameters: dnsname/mountname),配置 PersistentVolume 自动创建
  - **挂载点配置**: 配置 DNS 名称和挂载路径 (/fsx),生成 PersistentVolume YAML 模板供训练任务使用,配置 lustre client 内核模块
  - **性能验证**:
    - **单客户端测试**: 使用 fio 验证顺序读写吞吐量 ≥5GB/s (块大小 1MB, 队列深度 64)
    - **多客户端聚合**: 使用 4-8 个客户端 Pod 并发读取,验证聚合带宽 ≥20GB/s
    - **分布式训练模拟**: 模拟 PyTorch DataLoader 多进程读取场景,验证吞吐量稳定性
    - **S3 同步性能**: 确认满足 SC-005 性能目标 (S3 到 FSx 同步 1TB 数据 <10 分钟)
    - **调优方案**: 如吞吐量不达标,调整 FSx 吞吐量级别 (500 → 1000 MB/s/TiB) 或增加容量
    - **验证工具**: 提供性能测试脚本 (`infrastructure/tests/fsx-performance-test.sh`)
  - **生命周期策略**: 配置每日自动备份到 S3 (备份保留期 7 天),配置数据同步调度 (每小时增量同步到 S3),设置存储容量告警 (使用率 >80%)
  - **输出**: FSx 文件系统 ID、DNS 名称、挂载路径、StorageClass 名称
  - **依赖**: T008a (CDK 项目结构), T008b (VPC Stack, S3 Buckets Stack), T008c-1 (EKS 集群 - 包含 FSx CSI Driver), T008c-2 (GPU 节点组), T008c-3 (IAM 和安全配置), T008d (HyperPod Add-ons - 确保完整环境就绪)
  - **参考**: spec.md Technical Context "FSx for Lustre (训练数据), ≥5GB/s 吞吐量", FR-007 "支持 ≥10TB 数据集", SC-005 "S3 到 FSx 同步时间 <10分钟 (1TB 数据集)"
- [X] [T008f] Kubernetes NetworkPolicy 和 QoS 配置 - `infrastructure/k8s/network-policies/`,配置 HyperPod EKS 集群网络隔离和 QoS 策略:
  - **Pod 级网络隔离**: 使用 Kubernetes NetworkPolicy 实现训练任务 Pod 间的网络命名空间隔离
  - **默认拒绝策略**: 配置 default-deny NetworkPolicy,仅允许必需的流量 (Kueue API, Prometheus metrics, MLflow tracking)
  - **训练任务网络策略**: 为 PyTorchJob Pods 配置专用 NetworkPolicy,允许分布式训练通信 (EFA 网络) 和集群内部服务访问
  - **QoS 类别配置**: 配置 Pod QoS Class (Guaranteed 用于训练任务,确保资源预留和稳定性)
  - **带宽限制注解**: 使用 Kubernetes annotations 配置 Pod 网络带宽限制 (kubernetes.io/ingress-bandwidth, kubernetes.io/egress-bandwidth),防止单个任务占用过多带宽
  - **EFA 网络亲和性**: 配置 nodeSelector 和 tolerations 确保 EFA 网络拓扑优化生效
  - **监控和告警**: 集成 Prometheus NetworkPolicy Exporter 监控网络策略生效状态和连接拒绝事件
  - **性能验证**: 验证网络延迟 P99 <10ms,带宽利用率 >80% 性能目标
  - **参考**: spec.md FR-021 网络带宽管理和 QoS 策略 (依赖 T008c-1/T008c-2/T008c-3 HyperPod EKS 集群, T008d HyperPod Add-ons)

### ALB 和 TLS 配置
- [X] [T008i] [P] ALB Ingress 和 TLS 终止配置 - `infrastructure/cdk/stacks/alb_stack.py`,创建 Application Load Balancer Stack:
  - **ALB 配置**: 创建面向互联网的 ALB,部署到 T008b 创建的公有子网,配置健康检查和目标组
  - **TLS 终止**: 配置 HTTPS 监听器 (端口 443),绑定 AWS Certificate Manager (ACM) 证书,强制 TLS 1.2+ (禁用 TLS 1.0/1.1)
  - **HTTPS 重定向**: 配置 HTTP (端口 80) 到 HTTPS (端口 443) 自动重定向
  - **安全策略**: 使用 AWS 推荐的安全策略 (ELBSecurityPolicy-TLS-1-2-2017-01 或更新版本)
  - **WAF 集成**: 可选配置 AWS WAF (Web Application Firewall) 防护
  - **Kubernetes Ingress**: 创建 K8s Ingress 资源,配置 AWS Load Balancer Controller 注解,关联 ALB 和后端服务
  - **输出**: ALB DNS 名称、ACM 证书 ARN、Ingress 配置文件路径
  - **依赖**: T008a (CDK 项目结构), T008b (VPC Stack), T008c-1 (EKS 集群)
  - **参考**: spec.md FR-018 传输层加密要求, AWS ALB TLS 最佳实践

### 基础设施验证测试
- [X] [T008g] [P] HyperPod 基础设施验证测试 - 执行综合验证套件,确保基础设施就绪:
  - **集群健康检查**: 验证 EKS 集群状态 (kubectl cluster-info), 节点 Ready 状态 (所有节点), 控制平面健康 (kube-apiserver, etcd)
  - **GPU 节点验证**: 在 GPU 节点运行 nvidia-smi 测试 Pod, 验证 GPU 可见性和 CUDA 版本, 验证 GPU Operator 正常运行
  - **HyperPod Add-ons 功能测试**:
    - Training Operator: 提交测试 PyTorchJob (single-node hello-world), 验证 Job 状态转换为 Succeeded
    - Kueue: 验证 ClusterQueue 和 LocalQueue 状态为 Active, 提交测试 Workload 验证调度
    - Observability: 查询 Prometheus 指标 (up, node_cpu_seconds_total), 访问 Grafana 仪表盘
    - Elastic Agent: 验证 Elastic Agent Pod Running, 检查检查点管理日志
    - Spaces Add-on: 验证 Spaces CRD 注册, 检查 Spaces Controller Pod 状态
  - **FSx 存储验证**: 创建测试 PersistentVolumeClaim, 挂载到测试 Pod, 执行读写性能测试 (dd 命令), 验证 S3 Data Repository Association 同步
  - **网络连通性测试**: 验证 Pod 到 Internet 连通性 (curl https://aws.amazon.com), 验证 Pod 到 S3/CloudWatch PrivateLink 连通性, 验证 EFA 网络接口可用
  - **TLS/HTTPS 验证**: 验证 ALB HTTPS 端点可访问 (curl https://<alb-dns>), 验证 TLS 版本 ≥1.2 (openssl s_client), 验证 HTTP 自动重定向到 HTTPS, 验证 ACM 证书有效性
  - **输出**: 生成验证报告 (infrastructure-validation-report.md), 包含所有测试结果、失败项诊断建议、关键配置参数快照
  - **依赖**: T008c-1, T008c-2, T008c-3 (EKS 集群完整配置), T008d-1, T008d-2, T008d-3 (Add-ons), T008e (FSx), T008f (NetworkPolicy), T008i (ALB 和 TLS)
  - **参考**: aws-infrastructure.md CHK-TASK-019/020/021

**并行执行机会**:
- T001 (backend 结构) 和 T002 (frontend 结构) 可并行
- T001 完成后 → T004, T007 可并行
- T002 完成后 → T005 可开始
- T003, T006, T008 依赖 T001/T002 完成
- T000 (Phase 0 SDK 验证) → {T000-fallback (条件任务), T008a} → T008b → T008c-1 → {T008c-2, T008c-3} 可并行 → T008d-1 → {T008d-2, T008d-3} 可并行 → T008e → T008f (NetworkPolicy) → T008i (ALB 和 TLS) → T008g (串行,验证所有基础设施)

---

## Phase 2: Foundational - 基础设施 (23 tasks)

**目标**: 创建核心数据模型、企业级认证系统、审计日志基础设施、客户端封装和安全配置

### 核心数据表迁移
- [X] [T009] 创建 users 表迁移 - `backend/alembic/versions/20260114_221056_206d5baf77c1_create_core_tables_users_resource_.py`,字段: id (BigInt), username, email, iam_identity_id, role (enum), status, resource_quota_id (FK)
- [X] [T010] 创建 resource_quotas 表迁移 - `backend/alembic/versions/20260114_221056_206d5baf77c1_create_core_tables_users_resource_.py`,字段: id, name, quota_type, max_cpu_cores, max_gpu_count, max_memory_gb, max_storage_gb
- [X] [T010b] 创建 resource_limit_configs 表迁移 - `backend/alembic/versions/20260114_221056_206d5baf77c1_create_core_tables_users_resource_.py`,字段: id, config_name, role (enum: admin/project_manager/engineer/viewer), project_id (FK, nullable), max_gpu_per_job, max_cpu_per_job, max_memory_gb_per_job, max_storage_gb_per_job, max_nodes_per_job, priority_default (enum: high/medium/low), created_at, updated_at
- [X] [T010a] 创建 audit_logs 表迁移 - `backend/alembic/versions/20260114_221056_206d5baf77c1_create_core_tables_users_resource_.py`,字段: id, user_id (FK), operation_type (enum: create/update/delete/login/logout), resource_type (enum: training_job/dataset/model/user/quota/space), resource_id, request_data (JSON), response_data (JSON), ip_address, user_agent, status (enum: success/failed), created_at, expires_at (created_at + 90天)
- [X] [T010c] 创建 development_spaces 表迁移 - `backend/alembic/versions/20260114_221056_206d5baf77c1_create_core_tables_users_resource_.py`,字段: id (UUID), space_name (VARCHAR 255), owner_id (FK users), instance_type (enum: ml.t3.medium/ml.t3.large/ml.g4dn.xlarge), space_type (enum: jupyter/vscode/rstudio), status (enum: pending/running/stopped/failed/deleted), storage_size_gb (INT), lifecycle_config_arn (VARCHAR), sagemaker_space_arn (VARCHAR), created_at (TIMESTAMP), updated_at (TIMESTAMP), deleted_at (TIMESTAMP, nullable)
- [X] [T010d] 创建训练任务状态转换约束 - `backend/alembic/versions/20260114_221209_7778e77de8a6_create_training_job_state_transition_.py`,实现数据库级状态转换验证,防止非法状态转换 (如 Completed → Running):
  - **状态转换矩阵表**: 创建 `training_job_state_transitions` 表存储合法状态转换规则 (from_status, to_status, is_allowed),根据 spec.md Training Job State Model L533-547 定义的状态转换规则初始化数据
  - **CHECK 约束**: 在 `training_jobs` 表添加 CHECK 约束验证状态枚举值有效性 (Submitted/Running/Paused/Preempted/Completed/Failed)
  - **更新触发器**: 创建 BEFORE UPDATE 触发器 `validate_training_job_state_transition`,在状态更新前查询状态转换矩阵表,验证 (OLD.status → NEW.status) 是否合法,非法转换抛出异常并记录到审计日志
  - **终态保护**: 确保 Completed 和 Failed 状态不可转换到其他状态 (is_terminal=true 标记)
  - **性能优化**: 为状态转换矩阵表创建复合索引 (from_status, to_status),确保触发器性能开销 <5ms
  - **测试场景**: 验证合法转换 (Running → Paused)、阻止非法转换 (Completed → Running)、终态保护测试、并发更新一致性测试
  - **参考**: spec.md Training Job State Model 状态转换规则

### SQLAlchemy 模型
- [X] [T011] 创建 User 模型 - 领域实体 `backend/src/domain/entities/user.py` (纯业务对象) + ORM 模型 `backend/src/infrastructure/persistence/models/user_model.py` (SQLAlchemy),使用 Pydantic v2 schema 验证,关联 resource_quotas
- [X] [T011c] 创建 Space 模型 - 领域实体 `backend/src/domain/entities/space.py` + ORM 模型 `backend/src/infrastructure/persistence/models/space_model.py`,包含状态转换验证逻辑 (pending → running → stopped),关联 User (owner_id),支持 SageMaker Spaces ARN 存储,实现资源配额检查方法,提供空间生命周期管理接口 (start/stop/delete)
- [X] [T012] 创建 ResourceQuota 模型 - 领域实体 `backend/src/domain/entities/resource_quota.py` + ORM 模型 `backend/src/infrastructure/persistence/models/resource_quota_model.py`,包含配额验证逻辑
- [X] [T012b] 创建 ResourceLimitConfig 模型 - 领域实体 `backend/src/domain/entities/resource_limit_config.py` + ORM 模型 `backend/src/infrastructure/persistence/models/resource_limit_config_model.py`,包含限制验证逻辑,关联 User (通过 role),支持项目级和全局级配置 (project_id nullable),实现默认限制查询方法 (根据 user role + project 查找适用配置),提供配额检查和应用默认限制的服务接口
- [X] [T012a] 创建 AuditLog 模型 - 领域实体 `backend/src/domain/entities/audit_log.py` + ORM 模型 `backend/src/infrastructure/persistence/models/audit_log_model.py`,包含自动过期逻辑 (expires_at = created_at + 90天),关联 User,支持操作类型和资源类型枚举,实现审计日志查询优化

### 认证中间件
- [X] [T013] 实现基础认证中间件 - `backend/src/api/middleware/auth.py`,验证 IAM Identity Center token,提取用户信息

### 企业级认证扩展
- [X] [T013a] SSO集成实现 - `backend/src/api/middleware/sso.py`,集成AWS IAM Identity Center (SAML 2.0/OIDC),配置IdP元数据,实现用户自动映射和角色同步
- [X] [T013b] RBAC策略管理 - `backend/src/application/services/rbac_service.py`,定义角色层次 (admin/project_manager/engineer/viewer),实现基于资源的权限检查,集成Kubernetes RBAC
- [X] [T013c] 本地账号管理API - `backend/src/api/v1/endpoints/auth.py`,实现POST/PUT /auth/local-accounts,支持密码重置和账号启用/禁用,作为SSO不可用时的备用认证,包含以下密码安全要求:
  - **密码强度策略**: 最小长度 12 字符,必须包含大小写字母、数字和特殊字符
  - **密码哈希算法**: 使用 bcrypt (cost factor ≥12) 或 argon2id 存储密码哈希
  - **密码重置安全**: 生成临时令牌 (有效期 15 分钟),通过邮件发送重置链接,令牌使用后立即失效
  - **账号锁定策略**: 连续 5 次登录失败后锁定账号 30 分钟,防止暴力破解
  - **密码历史记录**: 记录最近 5 个密码哈希,禁止重复使用
  - **密码过期策略**: 密码有效期 90 天,过期后强制重置 (可选,管理员配置)
  - **审计日志集成**: 记录所有密码操作 (创建、重置、修改) 到 audit_logs 表
  - **安全响应头**: API 返回错误时使用通用消息 (避免泄露账号存在性信息)
  - **参考**: spec.md FR-015 企业级认证和 SC-015 安全标准

### AWS 客户端封装
- [X] [T014] [P] HyperPod SDK 客户端封装 - 接口 `backend/src/application/interfaces/hyperpod_client.py` (IHyperPodClient) + 实现 `backend/src/infrastructure/external/hyperpod/client.py`,封装 HyperPod Training 模块 API,使用 T000 验证的方法名实现训练任务生命周期管理 (提交、状态查询、暂停/恢复/终止),参考 `docs/hyperpod-sdk-reference.md` 获取准确的方法签名 (依赖 T000)
- [X] [T015] [P] S3 客户端封装 - 接口 `backend/src/application/interfaces/storage_service.py` (IStorageService) + 实现 `backend/src/infrastructure/external/s3/client.py`,封装 boto3 S3 操作 (upload_file, download_file, list_objects),支持 presigned URLs,继承 T008b 配置的 SSE-KMS 默认加密

### FastAPI 应用配置
- [ ] [T016] 配置 FastAPI 应用入口 - `backend/src/main.py`,注册路由,配置 CORS,集成认证中间件,配置 OpenAPI docs (TLS 终止由 T008i ALB 处理,应用无需配置 HTTPS)
- [ ] [T016b] 审计日志中间件 - `backend/src/api/middleware/audit.py`,拦截所有 API 请求,自动记录操作日志 (user_id, operation_type, resource_type, request/response data),异步写入数据库,确保审计完整性

### 前端基础配置
- [ ] [T017] [P] 配置 React Router - `frontend/src/App.tsx`,路由配置 (/training-jobs, /datasets, /admin, /reports, /ide)
- [ ] [T018] [P] 创建 Cloudscape Layout - `frontend/src/layouts/MainLayout.tsx`,使用 AppLayout 组件,配置侧边导航和顶部导航
- [ ] [T019] [P] 配置 Zustand store - `frontend/src/store/`,创建 authStore, trainingJobsStore, datasetsStore
- [ ] [T020] [P] 配置 TanStack Query - `frontend/src/lib/queryClient.ts`,配置全局 query client,设置重试策略和缓存策略

**并行执行机会**:
- 数据库迁移: T009 → T010 → T010b → T010a → T010c 串行执行 (确保 Alembic 版本号正确)
- SQLAlchemy 模型: T011, T011c, T012, T012b, T012a 可并行 (依赖 T009-T010c 完成)
- 认证系统: T013 → T013a, T013b, T013c (可并行) → T016 → T016b (依赖 T012a)
- 客户端封装: T014, T015 可并行
- 前端配置: T017, T018, T019, T020 可并行

---

## Phase 3: US1 (P1) - 训练任务管理 (33 tasks)

**用户故事**: 算法工程师提交和监控分布式训练任务,管理模型版本

### 数据表迁移
- [ ] [T021] 创建 training_jobs 表迁移 - `backend/alembic/versions/003_create_training_jobs.py`,字段: id, job_name, owner_id (FK users), instance_type, node_count, status (enum: submitted/running/paused/preempted/completed/failed), priority, training_config (JSON), created_at, updated_at
- [ ] [T022] 创建 checkpoints 表迁移 - `backend/alembic/versions/004_create_checkpoints.py`,字段: id, training_job_id (FK), checkpoint_name, storage_path, epoch, global_step, storage_tier (enum: nvme/fsx/s3), created_at
- [ ] [T022a] 创建 models 表迁移 - `backend/alembic/versions/005_create_models.py`,字段: id, model_name, version, training_job_id (FK), checkpoint_id (FK), model_uri (S3), registry_arn (SageMaker Model Registry), metrics (JSON: accuracy/loss), hyperparameters (JSON), framework (enum: pytorch/tensorflow), status (enum: training/registered/deployed/archived), created_at

### SQLAlchemy 模型
- [ ] [T023] 创建 TrainingJob 模型 - 领域实体 `backend/src/domain/entities/training_job.py` + ORM 模型 `backend/src/infrastructure/persistence/models/training_job_model.py`,包含状态转换验证 (submitted → running → paused/completed/failed),关联 User 和 Checkpoint
- [ ] [T024] 创建 Checkpoint 模型 - 领域实体 `backend/src/domain/entities/checkpoint.py` + ORM 模型 `backend/src/infrastructure/persistence/models/checkpoint_model.py`,包含存储层级自动迁移逻辑 (NVMe → FSx → S3)
- [ ] [T024a] 创建 Model 模型 - 领域实体 `backend/src/domain/entities/model.py` + ORM 模型 `backend/src/infrastructure/persistence/models/model_model.py`,包含版本比较逻辑,关联 TrainingJob 和 Checkpoint,支持 SageMaker Model Registry ARN 存储,实现模型生命周期管理

### 后端 API 端点 (基于 contracts/training-jobs-api.yaml)
- [ ] [T025] [US1] POST /training-jobs 端点实现 - `backend/src/api/v1/endpoints/training_jobs.py`,验证训练配置,检查资源配额,调用 HyperPod SDK 创建训练任务
- [ ] [T026] [US1] GET /training-jobs 端点实现 - 支持分页、过滤 (status, owner_id)、排序 (created_at, priority)
- [ ] [T027] [US1] GET /training-jobs/{id} 端点实现 - 返回训练任务详情,包含实时指标 (GPU 利用率,训练进度)
- [ ] [T028] [US1] PUT /training-jobs/{id} 端点实现 - 更新训练配置 (仅允许 priority, training_config 字段)
- [ ] [T029] [US1] DELETE /training-jobs/{id} 端点实现 - 软删除训练任务,终止 HyperPod 训练任务
- [ ] [T030] [US1] POST /training-jobs/{id}/pause 端点实现 - 暂停训练任务,保存检查点,更新状态为 paused
- [ ] [T031] [US1] POST /training-jobs/{id}/resume 端点实现 - 恢复训练任务,从最新检查点恢复,更新状态为 running
- [ ] [T031a] [US1] POST /models 端点实现 - `backend/src/api/v1/endpoints/models.py`,注册训练完成的模型,自动从 checkpoint 提升,集成 SageMaker Model Registry,记录模型元数据(metrics, hyperparameters)
- [ ] [T031b] [US1] GET /models 端点实现 - 支持分页、过滤 (training_job_id, status)、排序 (version, created_at),返回模型版本列表
- [ ] [T031c] [US1] GET /models/{id}/versions 端点实现 - 返回模型版本历史,支持版本对比 (metrics diff, hyperparameter changes)
- [ ] [T031d] [US1] POST /training-jobs/{id}/checkpoints 端点实现 - `backend/src/api/v1/endpoints/training_jobs.py`,支持用户手动触发检查点创建,验证任务状态 (仅 Running 状态可创建),调用 checkpoint_service 创建检查点,返回检查点 ID 和存储路径 (依赖 T038)

### 前端页面组件
- [ ] [T032] [US1] [P] 训练任务列表页面 - `frontend/src/pages/TrainingJobs/List.tsx`,使用 Cloudscape Table 组件,支持分页/过滤/排序,实时状态更新
- [ ] [T033] [US1] [P] 训练任务创建表单 - `frontend/src/pages/TrainingJobs/Create.tsx`,使用 Cloudscape Form 组件,验证训练配置 (实例类型,节点数,训练脚本路径),配额实时检查
- [ ] [T034] [US1] [P] 训练任务详情页面 - `frontend/src/pages/TrainingJobs/Detail.tsx`,展示训练配置、实时指标、日志流、检查点列表,支持暂停/恢复/终止操作
- [ ] [T035] [US1] [P] 训练状态监控组件 - `frontend/src/components/TrainingStatus.tsx`,实时显示 GPU 利用率、训练进度、损失曲线,30秒刷新间隔
- [ ] [T035a] [US1] [P] 模型版本管理页面 - `frontend/src/pages/Models/Versions.tsx`,使用 Cloudscape Table 展示模型版本历史,支持版本对比(metrics diff)、模型回滚、SageMaker Model Registry 同步状态显示

### HyperPod 集成服务
- [ ] [T036] [US1] HyperPodPytorchJob 集成逻辑 - `backend/src/application/services/hyperpod_service.py`,封装 HyperPod SDK 训练任务生命周期管理,使用 T000 验证的 Training 模块方法实现训练任务提交、暂停、恢复、终止功能,实现错误处理和重试机制,参考 `docs/hyperpod-sdk-reference.md`。如该模块不支持特定训练模式,MAY 使用 boto3 (SageMaker API) 或 kubernetes-client (直接操作 PyTorchJob CRD) 作为备选方案,但 MUST 提交例外申请并获得平台治理委员会批准,在代码中注释说明理由 (遵循宪章 Principle I.B) (依赖 T000, T014)
- [ ] [T036a] [US1] Gang Scheduling 行为验证 - `backend/tests/integration/test_gang_scheduling.py`,验证 FR-003 Gang Scheduling 机制正确工作:
  - **验证场景 1**: 提交多节点分布式训练任务 (≥2 节点),验证所有 Pods 在 60 秒内同时就绪
  - **验证场景 2**: 模拟部分 Pod 调度失败,验证任务状态正确转为 Failed 且已创建的 Pods 自动清理
  - **验证场景 3**: 验证 HyperPod Training Operator 默认 Gang Scheduling 配置生效
  - **监控指标**: 记录 Pod 就绪时间差,验证时间窗口 ≤60 秒
  - **测试工具**: 使用 pytest + kubernetes-client 查询 Pod 状态和事件
  - **参考**: spec.md FR-003 Gang Scheduling 机制 (依赖 T036, T008c-1/T008c-2/T008c-3 HyperPod 集群)
- [ ] [T037] [US1] 训练任务状态同步服务 - `backend/src/application/services/training_sync_service.py`,定时任务 (30秒) 同步 HyperPod 训练状态到数据库,使用 T000 验证的状态查询方法获取任务状态,处理状态转换事件,参考 `docs/hyperpod-sdk-reference.md`。如需细粒度状态监控,MAY 使用 kubernetes-client 查询 Kueue Workload 状态,但 MUST 提交例外申请并获得平台治理委员会批准,在代码中注释说明理由 (遵循宪章 Principle I.B) (依赖 T000, T036)
- [ ] [T037d] [US1] 抢占连续失败转 Failed 状态测试 - `backend/tests/integration/test_preemption_exhausted.py`,验证 FR-004 连续抢占失败机制:
  - **验证场景 1**: 模拟训练任务被连续抢占 3 次,验证第 3 次抢占后任务状态转为 Failed
  - **验证场景 2**: 验证 preemption_count 计数器正确累加 (每次抢占 +1)
  - **验证场景 3**: 验证失败分类正确记录 (failureCategory = "PreemptionExhausted")
  - **验证场景 4**: 验证自动停止重新排队,不再创建新的 Kueue Workload
  - **验证场景 5**: 验证告警通知发送给任务提交者和平台管理员
  - **测试工具**: 使用 pytest + kubernetes-client 模拟 Kueue Evicted condition
  - **参考**: spec.md L427-462 连续抢占失败逻辑 (依赖 T037)
- [ ] [T037c] [US1] 训练任务停滞检测服务 - `backend/src/application/services/stall_detection_service.py`,实现 FR-022 停滞检测机制:
  - **主指标监控**: 默认监控 Loss 指标,支持用户指定单一主检测指标 (Accuracy/Perplexity 等)
  - **停滞判定逻辑**: 主指标在可配置时间窗口 (默认 30 分钟) 内变化率 <0.1% 触发停滞告警
  - **辅助指标处理**: 其他指标异常仅记录日志供参考,不触发告警 (避免误报)
  - **配置灵活性**: 支持用户自定义检测窗口时长和变化率阈值
  - **禁用支持**: 支持用户禁用停滞检测 (适用于 GAN/RL 等 Loss 震荡场景)
  - **告警机制**: 停滞检测触发后发送邮件/消息通知给任务提交者和平台管理员
  - **终止选项**: 提供自动终止 (管理员配置) 或手动终止 (用户确认) 选项
  - **定时任务调度**: 每 5 分钟执行一次检测 (覆盖所有 Running 状态任务)
  - **参考**: spec.md FR-022 训练任务停滞检测机制 (依赖 T037 状态同步服务)
- [ ] [T037e] [US1] 停滞检测机制测试 - `backend/tests/integration/test_stall_detection.py`,验证 FR-022 停滞检测功能:
  - **验证场景 1**: 模拟 Loss 指标 30 分钟内变化率 <0.1%,验证停滞告警触发
  - **验证场景 2**: 验证用户指定主指标 (Accuracy) 时的停滞检测逻辑
  - **验证场景 3**: 验证禁用停滞检测配置 (disable_stall_detection: true) 生效
  - **验证场景 4**: 验证告警通知发送给任务提交者和管理员
  - **验证场景 5**: 验证主指标选择逻辑 (Loss → Accuracy → Perplexity 自动选择)
  - **测试工具**: 使用 pytest + MLflow API 模拟指标记录和查询
  - **参考**: spec.md FR-022 停滞检测策略 (依赖 T037c 停滞检测服务)
- [ ] [T037a] [US1] SageMaker Managed MLflow 集成 - `backend/src/application/services/mlflow_service.py`,部署 MLflow Tracking Server (使用 SageMaker Managed MLflow),配置 MLflow Tracking URI 环境变量注入,提供 Python SDK 示例代码 (`backend/examples/mlflow_training_example.py`),文档化指标记录最佳实践 (指标命名规范、记录频率、超参数追踪模式),实现 MLflow 实验查询 API 集成到前端监控页面
- [ ] [T037b] [US1] Prometheus Pushgateway 部署 (可选) - `infrastructure/monitoring/pushgateway.yaml`,部署 Pushgateway 服务到 EKS 集群 (仅用于实时告警场景),配置 Service 和环境变量 `PROMETHEUS_PUSHGATEWAY_URL` 注入,提供 Python SDK 示例代码 (`backend/examples/prometheus_metrics_example.py`),文档化与 MLflow 的职责分离和使用场景
- [ ] [T038] [US1] Checkpoint 自动保存逻辑 - `backend/src/application/services/checkpoint_service.py`,实现 FR-010 定义的 5 种检查点创建触发场景:
  - **(1) 定期自动创建**: 定时任务 (10-15 分钟间隔) 为 Running 状态的训练任务自动创建检查点
  - **(2) 训练中断**: 检测到训练任务 Pods 异常终止时立即触发检查点创建
  - **(3) 节点故障**: 检测到 PodsReady=False 且持续 >30 秒时触发检查点创建
  - **(4) 资源抢占**: 检测到 Kueue Evicted condition (reason: Preempted) 时立即触发检查点创建（在抢占前完成，超时 5 分钟则强制抢占）
  - **(5) 用户手动触发**: 提供服务接口支持 API 调用创建检查点 (参见 T031d)
  - **检查点保存**: 创建检查点并保存到初始存储位置 (优先 NVMe 本地存储,若不可用则保存到 FSx),记录检查点元数据 (创建时间、序号、存储路径、SHA-256 校验和)
  - **接口设计**: 提供 `create_checkpoint(job_id, trigger_type)` 接口创建检查点,提供 `list_checkpoints(job_id, filters)` 接口供 T038b 查询检查点列表
  - **职责边界**: T038 负责检查点创建和初始保存,不负责后续迁移 (迁移由 T038b 负责)
  - **参考**: spec.md FR-010 检查点触发场景映射
- [ ] [T038b-1] [US1] Checkpoint 分层迁移服务 - `backend/src/application/services/checkpoint_migration_service.py`,实现 FR-011 分层存储迁移策略:
  - **依赖接口**: 调用 T038 的 `list_checkpoints(job_id)` 接口获取检查点列表和元数据 (创建时间、序号、存储路径、校验和)
  - **热检查点管理**: 保留最近 3 个检查点在 NVMe 本地存储
  - **温检查点迁移**: 第 4-10 个检查点自动迁移到 FSx for Lustre
  - **冷检查点归档**: 创建序号 >10 或创建时间 >72 小时的检查点归档到 S3
  - **异步迁移执行**: 在检查点间隔期 (训练任务空闲时段) 执行迁移,避免影响训练性能
  - **存储满载处理**: NVMe/FSx 使用率 >90% 时触发紧急迁移至下一层,所有层均满载则告警并暂停新检查点创建 (保留最近 1 个)
  - **迁移失败回退**: 迁移失败时保留原位置检查点,记录失败日志,下次迁移周期重试 (最多 3 次),持续失败则触发告警
  - **完整性保护**: 创建时计算 SHA-256 校验和,恢复前验证完整性,若损坏则自动尝试上一个有效检查点并告警
  - **定时任务调度**: 每 10 分钟执行一次迁移检查和执行
  - **职责边界**: T038b-1 仅负责迁移已创建的检查点,不负责创建检查点 (创建由 T038 负责)
  - **参考**: spec.md FR-011 分层检查点存储策略, Edge Cases (检查点存储满载/检查点损坏处理) (依赖 T038)
- [ ] [T038b-2] [US1] S3 Lifecycle Policy IaC 配置 - `infrastructure/cdk/stacks/storage_stack.py`,实现 S3 检查点存储的生命周期自动化管理:
  - **生命周期规则 1 - 存储类转换**: 配置 S3 Lifecycle Rule,对象创建 30 天后自动转换为 Standard-IA（低频访问，成本节省 ~50%）
  - **生命周期规则 2 - 自动删除**: 对象创建 90 天后自动删除冷检查点（默认值，可通过 CDK context 参数配置）
  - **CDK 参数化配置**:
    - `checkpoint_retention_days` (默认 90): 冷检查点保留天数
    - `checkpoint_ia_transition_days` (默认 30): 转换为 Standard-IA 的天数
  - **对象标签过滤**: 仅对标签为 `checkpoint_type=cold` 的对象应用生命周期规则（避免误删热/温检查点）
  - **成本优化验证**: 在 CDK 部署前估算成本影响（Standard vs Standard-IA vs 删除后的成本对比）
  - **合规性说明**: 在 IaC 代码注释中文档化保留期选择依据（满足审计要求和模型回滚需求）
  - **职责边界**: T038b-2 仅负责 S3 基础设施配置,不负责检查点迁移逻辑 (迁移由 T038b-1 负责)
  - **依赖**: T008b (S3 Buckets Stack,提供 checkpoint bucket 名称和 ARN)
  - **参考**: spec.md FR-011 S3 生命周期策略要求
- [ ] [T038a] [US1] SageMaker Model Registry 集成 - `backend/src/application/services/model_registry_service.py`,封装 SageMaker Model Registry API,自动注册训练完成的模型,管理模型版本生命周期(注册→批准→部署→归档)

### 集成测试
- [ ] [T038c] [US1] 抢占时序SLA集成测试 - `backend/tests/integration/test_preemption_timing.py`,验证 FR-004 抢占时序保证:
  - **测试场景 1**: 触发低优先级任务被高优先级任务抢占 (使用 Kueue Priority 配置)
  - **测试场景 2**: 验证 checkpoint 在抢占触发后 5 分钟内保存完成 (监控 T038 的场景 4 触发时间戳)
  - **测试场景 3**: 验证被抢占任务的 Pod 在 30 秒内被释放 (调用 Kubernetes API 查询 Pod 状态)
  - **测试场景 4**: 验证任务状态正确转换为 Preempted (调用 T029 状态同步逻辑验证)
  - **测试场景 5**: 验证抢占后自动恢复成功 (checkpoint 恢复 + 训练继续)
  - **测试工具**: 使用 pytest + HyperPod SDK + Kubernetes Python Client
  - **估算**: 6h (SHOULD, Integration Test)
  - **依赖**: T022 (checkpoints 表), T024 (Checkpoint 模型), T029 (状态同步), T038 (checkpoint 自动保存逻辑)
  - **参考**: spec.md FR-004 抢占式调度时序要求

**并行执行机会**:
- 数据库迁移: T021, T022, T022a 可并行
- SQLAlchemy 模型: T023, T024, T024a 可并行 (依赖 T021, T022, T022a)
- 后端 API: T025-T031 可部分并行 (依赖 T023, T024) → T031a, T031b, T031c 可并行 (依赖 T024a)
- 前端页面: T032-T035 可并行 (依赖 T025-T031) → T035a (依赖 T031a-T031c)
- 服务逻辑: T036 → {T037, T037a} 可并行 → {T037c, T037b} 可并行 → {T038, T038a, T038b-1, T038b-2} 可并行 → T038c (集成测试)

**验收标准**:
- FR-001: 训练任务提交成功率 >95%
- FR-002: 训练任务启动时间 <2分钟
- FR-003: 状态同步延迟 <30秒
- SC-001: 支持 PyTorch DDP/FSDP/DeepSpeed ZeRO
- SC-002: 检查点保存成功率 >99%

---

## Phase 4: US2 (P1) - 数据集管理 (14 tasks)

**用户故事**: 数据工程师管理和版本控制训练数据集

### 数据表迁移
- [ ] [T039] 创建 datasets 表迁移 - `backend/alembic/versions/006_create_datasets.py`,字段: id, name, version, storage_type (enum: s3/fsx), storage_uri, dataset_type (enum: image/text/audio/video), size_bytes, owner_id (FK users), created_at, updated_at

### SQLAlchemy 模型
- [ ] [T040] 创建 Dataset 模型 - 领域实体 `backend/src/domain/entities/dataset.py` + ORM 模型 `backend/src/infrastructure/persistence/models/dataset_model.py`,包含版本控制逻辑,关联 User,支持元数据存储

### 后端 API 端点 (基于 contracts/datasets-api.yaml)
- [ ] [T041] [US2] POST /datasets 端点实现 - `backend/src/api/v1/endpoints/datasets.py`,验证数据集元数据,生成 S3 presigned upload URL,创建数据集记录
- [ ] [T042] [US2] GET /datasets 端点实现 - 支持分页、过滤 (dataset_type, owner_id)、排序 (created_at, size_bytes)
- [ ] [T043] [US2] GET /datasets/{id} 端点实现 - 返回数据集详情,包含版本历史、存储信息、使用统计
- [ ] [T044] [US2] PUT /datasets/{id} 端点实现 - 更新数据集元数据 (name, dataset_type, description)
- [ ] [T045] [US2] DELETE /datasets/{id} 端点实现 - 软删除数据集,清理 S3/FSx 存储 (可选)
- [ ] [T046] [US2] POST /datasets/{id}/versions 端点实现 - 创建数据集新版本,复制或链接存储路径,更新版本号

### 存储集成服务
- [ ] [T047] [US2] S3 上传集成 - `backend/src/application/services/dataset_upload.py`,实现分片上传,计算 MD5 校验和,支持断点续传
- [ ] [T048] [US2] FSx for Lustre 路径管理 - `backend/src/application/services/fsx_service.py`,管理 FSx 挂载路径,自动同步 S3 到 FSx (≥5GB/s 吞吐量),数据预热逻辑

### 前端页面组件
- [ ] [T049] [US2] [P] 数据集列表页面 - `frontend/src/pages/Datasets/List.tsx`,使用 Cloudscape Table,支持搜索/过滤/排序,显示存储类型和大小
- [ ] [T050] [US2] [P] 数据集创建表单 - `frontend/src/pages/Datasets/Create.tsx`,使用 Cloudscape Form,支持文件上传 (drag & drop),显示上传进度,验证数据集格式
- [ ] [T051] [US2] [P] 数据集版本管理页面 - `frontend/src/pages/Datasets/Versions.tsx`,显示版本历史时间线,支持版本对比和回滚
- [ ] [T052] [US2] [P] 文件上传组件 - `frontend/src/components/FileUpload.tsx`,实现分片上传到 S3,显示上传进度条,支持取消和重试

**并行执行机会**:
- 数据库迁移: T039 独立
- SQLAlchemy 模型: T040 依赖 T039
- 后端 API: T041-T046 可部分并行 (依赖 T040)
- 存储服务: T047, T048 可并行
- 前端页面: T049-T052 可并行 (依赖 T041-T046)

**验收标准**:
- FR-006: 数据集上传速度 ≥100MB/s
- FR-007: 支持 ≥10TB 数据集
- FR-008: 版本控制支持 ≥100 个版本
- SC-005: S3 到 FSx 同步时间 <10分钟 (1TB 数据集)

---

## Phase 5: US3 (P1) - 资源配额和集群监控 (19 tasks)

**用户故事**: 平台管理员配置资源配额、监控集群和查询审计日志

### 数据表迁移
- [ ] [T053] 创建 hyperpod_clusters 表迁移 - `backend/alembic/versions/006_create_hyperpod_clusters.py`,字段: id, cluster_name, cluster_arn, region, status (enum: active/inactive/error), instance_types (JSON), capacity (JSON), created_at, updated_at

### SQLAlchemy 模型
- [ ] [T054] 创建 HyperPodCluster 模型 - 领域实体 `backend/src/domain/entities/hyperpod_cluster.py` + ORM 模型 `backend/src/infrastructure/persistence/models/hyperpod_cluster_model.py`,包含集群容量计算逻辑,关联 TrainingJob

### 后端 API 端点 (基于 contracts/users-api.yaml, resource-quotas-api.yaml, monitoring-api.yaml)
- [ ] [T055] [US3] GET /users 端点实现 - `backend/src/api/v1/endpoints/users.py`,支持分页、过滤 (role, status)、排序 (created_at)
- [ ] [T056] [US3] POST /users 端点实现 - 验证用户信息,创建 IAM Identity Center 用户,分配默认配额
- [ ] [T057] [US3] PUT /users/{id} 端点实现 - 更新用户角色、状态、配额关联
- [ ] [T058] [US3] GET /resource-quotas 端点实现 - `backend/src/api/v1/endpoints/resource_quotas.py`,返回所有配额模板
- [ ] [T059] [US3] POST /resource-quotas 端点实现 - 创建配额模板,验证配额限制 (CPU, GPU, Memory, Storage)
- [ ] [T060] [US3] PUT /resource-quotas/{id} 端点实现 - 更新配额限制,触发用户通知
- [ ] [T061] [US3] GET /monitoring/metrics 端点实现 - `backend/src/api/v1/endpoints/monitoring.py`,查询 Prometheus 指标 (GPU 利用率,集群容量,任务队列长度),支持时间范围过滤
- [ ] [T061a] [US3] GET /audit-logs 端点实现 - `backend/src/api/v1/endpoints/audit_logs.py`,支持分页、过滤 (user_id, operation_type, resource_type, time_range)、排序 (created_at),返回审计日志列表,管理员权限
- [ ] [T061b] [US3] DELETE /audit-logs/cleanup 端点实现 - 清理过期审计日志 (expires_at < now),管理员权限,定时任务调用,记录清理统计
  - **职责**: 提供 API 接口供自动清理服务 (T102a) 或管理员手动调用
  - **输出**: 返回清理统计 (清理条数、执行耗时、失败记录数)

### 监控集成服务
- [ ] [T062] [US3] Prometheus 指标采集集成 - `backend/src/application/services/prometheus_service.py`,封装 Prometheus HTTP API,查询 HyperPod Observability Add-on 指标,实现 ≤30秒刷新频率:
  - **存储容量监控 (FR-020)**: 采集 FSx for Lustre 和 S3 存储使用率指标,配置双阈值告警 (80% 警告/90% 严重),集成 CloudWatch Alarms 发送通知
  - **网络性能监控 (FR-021)**: 采集 EFA 网络吞吐量、延迟指标 (node_network_receive/transmit_bytes_total),监控 Pod 间网络延迟 P99,配置告警 (延迟 >10ms 或带宽利用率 <80% 触发)
  - **告警规则配置**: 创建 Prometheus AlertManager 规则 (`infrastructure/prometheus/alerts/storage-alerts.yaml`, `infrastructure/prometheus/alerts/network-alerts.yaml`),定义存储和网络告警条件
  - **参考**: spec.md FR-020 存储容量监控, FR-021 网络带宽管理和 QoS 策略
- [ ] [T063] [US3] Grafana 仪表盘配置 - 创建 Grafana dashboard JSON 配置 (`infrastructure/grafana/dashboards/hyperpod-overview.json`),展示集群健康、资源利用率、训练任务分布
- [ ] [T068] [US3] 集群健康检查服务 - `backend/src/application/services/cluster_health_service.py`,定时任务 (1分钟) 检查 HyperPod 集群状态,更新 hyperpod_clusters 表,触发告警

### 前端页面组件
- [ ] [T064] [US3] [P] 用户管理页面 - `frontend/src/pages/Admin/Users.tsx`,使用 Cloudscape Table,支持用户创建/编辑/禁用,显示配额使用情况
- [ ] [T065] [US3] [P] 资源配额管理页面 - `frontend/src/pages/Admin/Quotas.tsx`,使用 Cloudscape Form,支持配额模板创建/编辑,显示配额分配统计
- [ ] [T066] [US3] [P] 集群监控仪表盘 - `frontend/src/pages/Admin/ClusterMonitoring.tsx`,嵌入 Grafana 仪表盘 (iframe),显示实时指标图表,支持时间范围选择
- [ ] [T067] [US3] [P] 实时指标图表组件 - `frontend/src/components/MetricsCharts.tsx`,使用 Recharts 渲染 Prometheus 指标,支持多种图表类型 (折线图、柱状图、饼图)
- [ ] [T067a] [US3] [P] 审计日志查询页面 - `frontend/src/pages/Admin/AuditLogs.tsx`,使用 Cloudscape Table 展示审计日志,支持高级过滤 (用户、操作类型、资源类型、时间范围)、导出 CSV、管理员权限

**并行执行机会**:
- 数据库迁移: T053 独立
- SQLAlchemy 模型: T054 依赖 T053
- 后端 API: T055-T061 可部分并行 (依赖 T054) → T061a, T061b 可并行
- 监控服务: T062, T063, T068 可并行
- 前端页面: T064-T067 可并行 (依赖 T055-T061) → T067a (依赖 T061a)

**验收标准**:
- FR-012: 配额检查延迟 <100ms
- FR-013: 集群监控刷新频率 ≤30秒
- FR-014: 支持 ≥1000 并发用户
- FR-020: 存储容量告警触发准确率 100% (80%/90% 双阈值)
- FR-021: 网络延迟 P99 <10ms,带宽利用率 >80%
- SC-008: Prometheus 指标保留期 ≥30天

---

## Phase 6: US4 (P2) - 资源使用报表和成本分析 (13 tasks)

**用户故事**: 项目经理查看资源使用报表和成本分析,验证成本计算准确率

**依赖**: US1, US2, US3 完成 (需要训练任务、数据集、配额数据)

### 成本计算服务
- [ ] [T069] [US4] 成本计算引擎核心逻辑 - `backend/src/application/services/cost_calculator.py`,基于 instance_type, node_count, training_duration 计算训练成本,实现成本累加和分摊逻辑,支持多维度成本分析 (compute/storage/network)
- [ ] [T069a] [US4] AWS Cost Explorer 集成 - `backend/src/infrastructure/external/aws/cost_explorer_client.py`,封装 AWS Cost Explorer API,获取实际账单数据 (EC2, S3, FSx, EBS),支持按资源标签过滤成本数据,缓存策略 (1小时刷新)
- [ ] [T069b] [US4] 训练成本定价模型 - `backend/src/application/services/pricing_model.py`,维护 HyperPod 实例定价表 (p4d.24xlarge, p5.48xlarge, trn1.32xlarge),FSx for Lustre 存储定价 (按吞吐量和容量),S3 存储和数据传输定价,网络传输成本计算
- [ ] [T069c] [US4] 成本准确率验证测试 - `backend/tests/test_cost_accuracy.py`,对比计算成本 vs AWS Cost Explorer 实际账单,误差率计算 (目标 <2%),回归测试 (使用历史训练任务数据),准确率监控告警 (误差 >2% 触发)
  - **依赖**: T069 (成本计算引擎), T069a (Cost Explorer 集成), T069b (定价模型), T070 (资源使用聚合查询)
  - **测试数据**: 使用 T070 聚合的历史训练任务数据 (至少 30 天)
- [ ] [T070] [US4] 资源使用聚合查询 - `backend/src/application/services/usage_aggregator.py`,使用 SQLAlchemy aggregation functions 聚合用户/项目资源使用,支持按时间维度分组 (day/week/month)

### 后端 API 端点
- [ ] [T071] [US4] GET /reports/resource-usage 端点 - `backend/src/api/v1/endpoints/reports.py`,查询资源使用报表,支持时间范围、用户/项目过滤,返回 CPU/GPU/Storage 使用统计
- [ ] [T072] [US4] GET /reports/cost-analysis 端点 - 查询成本分析报表,支持时间范围、成本类型 (compute/storage/network) 过滤,返回成本趋势和预测

### CloudWatch Logs 集成
- [ ] [T073] [US4] CloudWatch Logs 集成 - `backend/src/infrastructure/external/aws/cloudwatch_client.py`,封装 CloudWatch Logs Insights API,查询训练任务日志,支持 30天留存策略

### 前端页面组件
- [ ] [T074] [US4] [P] 资源使用报表页面 - `frontend/src/pages/Reports/ResourceUsage.tsx`,使用 Cloudscape Container,展示资源使用图表和表格,支持导出 CSV
- [ ] [T075] [US4] [P] 成本分析仪表盘 - `frontend/src/pages/Reports/CostAnalysis.tsx`,展示成本趋势图、成本分布饼图、成本预测,支持钻取到用户/项目级别
- [ ] [T076] [US4] [P] 时间范围选择器组件 - `frontend/src/components/DateRangePicker.tsx`,使用 Cloudscape DateRangePicker,支持预设时间范围 (Last 7 days, Last 30 days, Custom)
- [ ] [T077] [US4] [P] 成本趋势图表组件 - `frontend/src/components/CostTrendChart.tsx`,使用 Recharts 渲染成本趋势折线图,支持对比上一周期

### 报表导出功能
- [ ] [T078] [US4] 报表导出功能 - `backend/src/application/services/report_export_service.py`,实现 CSV/PDF 导出,使用 pandas 和 reportlab,支持自定义报表模板

**并行执行机会**:
- 成本计算服务: T069, T069a, T069b, T070 可并行 → T069c (依赖 T069, T069a, T069b, T070)
- 后端 API: T071, T072, T073 可部分并行 (依赖 T069, T070)
- 前端页面: T074-T077 可并行 (依赖 T071, T072)
- 报表导出: T078 依赖 T071, T072

**验收标准**:
- FR-018: 报表生成时间 <5秒
- FR-019: 成本计算准确率 >98%
- SC-012: 支持 ≥12个月历史数据查询

---

## Phase 7: US5 (P2) - 在线开发环境 (SageMaker Spaces) (15 tasks)

**用户故事**: 算法工程师使用 Amazon SageMaker Spaces 在线开发环境 (JupyterLab/VS Code)

**依赖**: Phase 1 基础设施完成 (T008c-1/2/3 HyperPod EKS 集群, T008d Spaces Add-on, T000 SDK 方法验证), Phase 2 基础认证完成 (T013)

**不依赖**: US1 训练任务管理逻辑 (T036-T038)

**可以并行**: US5 可以与 US1/US2/US3/US4 并行开发 (仅依赖 Phase 1-2 基础设施)

**技术选型**: Amazon SageMaker Spaces Add-on (JupyterLab/VS Code IDE)

### 数据表迁移
- [ ] [T079] [US5] 在线开发环境表迁移 - `backend/alembic/versions/007_create_dev_environments.py`,字段: id, environment_name, owner_id (FK users), ide_type (enum: jupyterlab/vscode), sagemaker_space_name, sagemaker_space_arn, instance_type (enum: ml.g5.xlarge/ml.g5.2xlarge,默认 ml.g5.xlarge,遵循 spec.md User Story 5 资源配额定义), status (enum: Pending/InService/Stopping/Stopped/Failed), studio_url, created_at, updated_at

### SQLAlchemy 模型
- [ ] [T080] [US5] DevEnvironment 模型 - 领域实体 `backend/src/domain/entities/dev_environment.py` + ORM 模型 `backend/src/infrastructure/persistence/models/dev_environment_model.py`,包含 SageMaker Space 生命周期管理 (Pending → InService → Stopped),关联 User,存储 Space ARN 和 Studio URL

### 后端 API 端点
- [ ] [T081] [US5] POST /ide/sessions 端点实现 - `backend/src/api/v1/endpoints/ide.py`,验证 IDE 配置,调用 SageMaker Spaces API 创建 Space,配置实例类型 (ml.g5.xlarge 默认/ml.g5.2xlarge,遵循 spec.md User Story 5 资源配额定义),验证用户配额 (GPU/CPU/内存,计入 FR-008 整体配额),返回 SageMaker Studio URL
- [ ] [T082] [US5] GET /ide/sessions 端点实现 - 支持分页、过滤 (status, owner_id)、排序 (created_at)
- [ ] [T083] [US5] GET /ide/sessions/{id} 端点实现 - 返回在线开发环境详情,包含 SageMaker Studio URL、Space 状态、实例类型、资源使用
- [ ] [T084] [US5] DELETE /ide/sessions/{id} 端点实现 - 调用 SageMaker DeleteSpace API 停止在线开发环境,清理 Space 资源

### SageMaker Spaces 集成服务
- [ ] [T085] [US5] SageMaker Spaces 集成 - `backend/src/application/services/sagemaker_spaces_service.py`,封装 `sagemaker-hyperpod.space` 模块 API,使用 T000 验证的 Space 模块方法实现 Space 创建、删除、查询功能,配置生命周期脚本 (Lifecycle Configuration) 预装常用库,管理 Space 状态转换,参考 `docs/hyperpod-sdk-reference.md`。如 SDK 不支持特定配置,MAY 使用 boto3 调用 SageMaker Spaces API 作为备选,但 MUST 提交例外申请并获得平台治理委员会批准,在代码中注释说明理由 (遵循宪章 Principle I.B) (依赖 T000)
- [ ] [T085a] [US5] SageMaker Spaces 启动性能配置 - `backend/src/application/services/sagemaker_lifecycle_service.py`,配置 SageMaker Studio 生命周期脚本,预装常用 Python 库 (pip install pytorch transformers),选择合适的实例类型 (ml.g5.xlarge 默认/ml.g5.2xlarge 高性能场景,遵循 spec.md User Story 5 资源配额定义),配置 EFS 持久化存储避免重装,目标启动时间 <3分钟
- [ ] [T085b] [US5] SageMaker Spaces 启动性能监控 - `backend/src/application/services/sagemaker_metrics_service.py`,集成 CloudWatch Metrics 监控 Space 启动时间,记录 CreateSpace API 调用到 InService 状态的耗时,P95/P99 启动时间统计,启动超时告警 (>3分钟触发)
- [ ] [T085c] [US5] SageMaker Spaces 启动性能测试 - `backend/tests/test_sagemaker_spaces_performance.py`,端到端启动时间测试 (目标 <3分钟),并发启动压力测试 (≥50 并发 Space),不同实例类型启动时间对比,性能回归测试 (CI/CD 集成)
- [ ] [T086] [US5] SageMaker Studio 镜像配置 - `backend/src/application/services/sagemaker_image_service.py`,使用 SageMaker Studio 官方镜像 (Data Science, PyTorch, TensorFlow),支持自定义镜像注册到 SageMaker Image Registry,配置镜像版本管理
- [ ] [T090] [US5] SageMaker Space 状态同步 - `backend/src/application/services/sagemaker_sync_service.py`,定时任务 (30秒) 调用 DescribeSpace API 同步状态到数据库,处理 InService/Pending/Failed 状态转换

### 前端页面组件
- [ ] [T087] [US5] [P] IDE 启动页面 - `frontend/src/pages/IDE/Launch.tsx`,使用 Cloudscape Form,选择 IDE 类型 (JupyterLab/VS Code)、实例类型 (ml.g5.xlarge 默认/ml.g5.2xlarge,显示资源规格: CPU/内存/GPU,遵循 spec.md User Story 5 资源配额定义)、SageMaker Studio 镜像,显示启动进度和预估启动时间
- [ ] [T088] [US5] [P] 在线开发环境列表页面 - `frontend/src/pages/IDE/Sessions.tsx`,使用 Cloudscape Table,显示 SageMaker Space 列表,支持启动/停止/删除操作,显示 Space 状态和启动耗时
- [ ] [T089] [US5] [P] IDE 嵌入组件 - `frontend/src/components/IDEFrame.tsx`,使用 iframe 嵌入 SageMaker Studio URL (JupyterLab/VS Code),支持全屏模式

**并行执行机会**:
- 数据库迁移: T079 独立
- SQLAlchemy 模型: T080 依赖 T079
- 后端 API: T081-T084 可部分并行 (依赖 T080)
- SageMaker Spaces 服务: T085, T085a, T086, T090 可并行 → T085b (部署监控) → T085c (执行测试并验证监控数据)
  - **理由**: T085c 测试需要 T085b 监控指标来验证启动时间 P95/P99，确保测试结果可观测
- 前端页面: T087-T089 可并行 (依赖 T081-T084)

**验收标准**:
- FR-023: IDE 启动时间 <3分钟
- FR-024: 支持 ≥50 并发在线开发环境
- SC-015: 在线开发环境自动保存间隔 ≤5分钟
  - **技术实现**: SageMaker HyperPod Spaces Add-on 内置自动保存功能
    - JupyterLab: 默认 120秒 (2分钟) 自动保存到 EFS
    - VS Code: 默认 1秒 (afterDelay) 自动保存到 EFS
    - 数据持久化到 HyperPod 集群共享 EFS (`/home/sagemaker-user/`)
    - 会话重启后自动恢复,满足 ≤5分钟要求
  - **平台实现**: T085 (SageMaker Spaces 集成) 已覆盖 Space 创建和管理

---

## Phase 8: Polish & Cross-cutting - 质量保障、GitOps 和横向功能 (21 tasks)

**目标**: 确保系统质量、稳定性、可维护性、安全合规性、审计日志保留策略和 GitOps 持续部署

### 单元测试
- [ ] [T091] [P] 后端单元测试覆盖 - 使用 pytest,覆盖所有 API 端点、服务逻辑、数据模型,目标覆盖率 ≥80% (`backend/tests/`)
- [ ] [T092] [P] 前端单元测试覆盖 - 使用 Jest + React Testing Library,覆盖所有页面组件、业务逻辑,目标覆盖率 ≥70% (`frontend/tests/`)

### 集成测试 (API Contract Validation)
- [ ] [T093] API Contract 集成测试 - training-jobs-api.yaml - 使用 pytest + OpenAPI validator,验证 POST/GET/PUT/DELETE /training-jobs 端点与 contract 一致性 (`backend/tests/integration/test_training_jobs_contract.py`)
- [ ] [T094] API Contract 集成测试 - datasets-api.yaml - 验证 /datasets 端点与 contract 一致性
- [ ] [T095] API Contract 集成测试 - users-api.yaml, resource-quotas-api.yaml - 验证 /users, /resource-quotas 端点与 contract 一致性

### 文档生成
- [ ] [T096] [P] OpenAPI 文档生成 - 配置 FastAPI 自动生成 OpenAPI 3.0 规范,集成 Swagger UI (`/docs`) 和 ReDoc (`/redoc`)

### 错误处理和重试逻辑
- [ ] [T097] [P] 统一错误处理中间件 - `backend/src/api/middleware/error_handler.py`,捕获所有异常,返回标准化错误响应 (RFC 7807 Problem Details),记录错误日志
- [ ] [T098] [P] 请求重试逻辑 - `frontend/src/lib/apiClient.ts`,使用 TanStack Query retry 机制,配置指数退避策略 (1s, 2s, 4s),最多重试 3 次
- [ ] [T099] [P] 前端错误边界组件 - `frontend/src/components/ErrorBoundary.tsx`,捕获 React 组件错误,显示友好错误页面,支持错误上报

### 日志和监控
- [ ] [T100] 日志格式标准化 - 使用 structlog 配置 JSON 结构化日志,包含 trace_id, user_id, request_id 字段,输出到 CloudWatch Logs
- [ ] [T101] CloudWatch Logs 配置验证 - 验证 30天日志留存策略,配置日志组 (/aws/hyperpod/training-platform),创建 CloudWatch Logs Insights 查询模板
- [ ] [T101a] 加密合规性验证 - 验证所有 S3 存储桶启用 SSE-KMS 加密,验证 API 端点强制 TLS 1.2+,生成加密审计报告,确保符合 FR-018 要求
- [ ] [T102] 性能监控埋点 - 使用 FastAPI middleware 记录 API 延迟,上报到 CloudWatch Metrics,配置告警 (P95 延迟 >500ms)
- [ ] [T102a] 审计日志自动清理服务 - `backend/src/application/services/audit_cleanup_service.py`,配置定时任务 (使用 APScheduler 或 Celery Beat,每日凌晨 2:00 执行),调用 DELETE /audit-logs/cleanup API (T061b),记录清理统计 (清理条数、执行耗时、失败记录数),CloudWatch Logs 记录清理事件 (级别 INFO,包含清理时间和统计),配置清理失败告警 (连续 3 天失败触发),确保符合 FR-017 保留策略 ≥90天
  - **职责**: 定时任务调度和执行监控,不负责实际清理逻辑 (委托给 T061b)
  - **依赖**: T061b (cleanup API)

### 前端性能优化
- [ ] [T103] 前端性能优化 - 实现 React.lazy() 代码分割,路由级别懒加载,使用 Vite 构建优化 (tree shaking, minification),目标首屏加载 <3秒

### 无障碍访问
- [ ] [T104] 无障碍访问测试 - 使用 axe-core 测试 WCAG 2.1 AA 级别合规性,修复键盘导航、屏幕阅读器、颜色对比度问题

### 用户引导测试
- [ ] [T104a] 用户引导 E2E 测试 - `frontend/tests/e2e/test_user_onboarding.spec.ts`,验证 SC-005 首次用户引导完成率 ≥90%:
  - **引导流程测试**: 模拟首次登录用户,验证引导向导正确显示和步骤流转
  - **关键功能覆盖**: 验证引导覆盖核心功能 (创建训练任务、上传数据集、查看监控)
  - **完成率统计**: 集成前端埋点,统计引导各步骤完成率和跳出率
  - **可用性验证**: 验证引导提示清晰易懂,支持跳过和重新开始
  - **测试工具**: 使用 Playwright 执行 E2E 测试,生成引导完成率报告
  - **参考**: spec.md SC-005 用户引导完成率 ≥90%

### UI 组件库合规性
- [ ] [T106] Cloudscape 组件库合规性审计 - 扫描前端代码 (`frontend/src/`),验证所有 UI 组件来自 @cloudscape-design/components,禁止使用 MUI/Ant Design/自定义实现,使用 ESLint 规则 (no-restricted-imports) 自动检测,生成合规性报告 (不合规组件列表、违规文件路径、修复建议),CI/CD 集成 (不合规则 PR 失败)

### 用户手册和部署文档
- [ ] [T105] 用户手册和部署文档 - 创建用户手册 (`docs/user-guide.md`),部署文档 (`docs/deployment.md`),包含环境配置、故障排查、最佳实践

### GitOps 工作流和持续部署
- [ ] [T105a] ArgoCD 安装和配置 - `infrastructure/argocd/install.yaml`,在 EKS 集群安装 ArgoCD,配置 ArgoCD Server 访问权限,创建 ArgoCD Projects (dev/staging/prod),配置 RBAC 策略
- [ ] [T105b] ArgoCD Application 配置 - `infrastructure/argocd/applications/`,创建 ArgoCD Application 清单 (backend-app.yaml, frontend-app.yaml),配置 Git 仓库源 (auto-sync, self-heal),定义目标集群和命名空间,配置同步策略和健康检查
- [ ] [T105c] Kubernetes 部署清单 - `infrastructure/k8s/`,编写 Deployment (backend/frontend), Service (ClusterIP/LoadBalancer), Ingress (ALB), ConfigMap (环境变量), Secret (敏感信息), HPA (自动扩缩容) 清单,遵循 Kubernetes 最佳实践
- [ ] [T105d] CI/CD 流水线集成 - `.github/workflows/deploy.yaml`,配置 GitHub Actions 流水线,实现 build → test → push image → update Git manifest → ArgoCD auto-sync 完整流程,支持多环境部署 (dev/staging/prod)
- [ ] [T105e] 配置漂移检测和审计追踪 - `infrastructure/gitops/monitoring/`,配置 ArgoCD 同步状态监控 (SyncStatus, Health Status),设置漂移告警规则 (Slack/邮件通知),记录配置变更审计日志 (Git commit SHA, 操作者, 变更时间),定时检查 (5分钟间隔) 并生成漂移报告,集成到 Grafana 仪表盘

**并行执行机会**:
- 单元测试: T091, T092 可并行
- 集成测试: T093, T094, T095 可并行
- 文档和错误处理: T096, T097, T098, T099 可并行
- 日志和监控: T100, T101 可并行 → T101a (依赖 T101) → T102, T102a 可并行
- 前端优化和测试: T103, T104, T104a 可并行
- GitOps 工作流: T105a → T105b, T105c, T105d 可并行 (依赖 T105a) → T105e (依赖 T105b)

---

## 依赖关系图

### User Story 级别依赖
```
Setup (Phase 1)
  ↓
Foundational (Phase 2)
  ↓
├── US1 (Phase 3, P1) ─┬─→ US4 (Phase 6, P2)
│                       │
├── US2 (Phase 4, P1) ─┤
│                       │
└── US3 (Phase 5, P1) ─┴─→ US4 (Phase 6, P2)
                        ↓
                      US5 (Phase 7, P2) ← US1
                        ↓
                    Polish (Phase 8)
```

### 关键依赖说明
1. **Foundational → US1/US2/US3**: 所有用户故事依赖基础表 (users, resource_quotas) 和认证中间件
2. **US1 + US2 + US3 → US4**: 成本分析依赖训练任务、数据集、配额数据的完整性
3. **US1 → US5**: IDE 环境依赖训练任务基础设施 (HyperPod 集群、容器镜像管理)
4. **US1/US2/US3 可并行**: P1 优先级的三个核心故事相互独立,可并行开发

### 并行开发前置条件

**Phase 3 (US1 训练任务) 可以启动的条件**:
- ✅ Phase 1 完成: T008c-1/2/3 (HyperPod EKS 集群), T008d (HyperPod Add-ons), T000 (SDK 方法验证)
- ✅ Phase 2 完成: T009-T012 (核心数据模型), T013 (认证中间件), T014 (HyperPod SDK 客户端)

**Phase 4 (US2 数据集) 可以启动的条件**:
- ✅ Phase 1 完成: T008b (S3 Buckets Stack 含加密), T008e (FSx Stack)
- ✅ Phase 2 完成: T009-T012 (核心数据模型), T013 (认证中间件), T015 (S3 客户端封装)

**Phase 5 (US3 配额监控) 可以启动的条件**:
- ✅ Phase 1 完成: T008d (Kueue 调度器 + Observability Add-on)
- ✅ Phase 2 完成: T009-T012 (核心数据模型), T013 (认证中间件)

**接口约定**: Phase 3/4/5 并行开发时,需要提前约定 API 接口规范 (contracts/*.yaml),避免集成冲突

---

## 并行执行示例

### Phase 3 (US1) 并行执行策略
```
并行组1 (数据库): T021, T022 (同时执行)
  ↓
并行组2 (模型): T023, T024 (依赖组1,同时执行)
  ↓
并行组3 (后端 API): T025, T026, T027, T028, T029, T030, T031 (依赖组2,部分并行)
  ↓
并行组4 (前端页面): T032, T033, T034, T035 (依赖组3,同时执行)
  ↓
串行 (服务逻辑): T036 → T037 → T038 (依赖组3,需串行)
```

**时间估算**: 串行 36 小时 → 并行 18 小时 (节省 50%)

### Phase 4 (US2) 并行执行策略
```
串行: T039 (数据库迁移)
  ↓
串行: T040 (SQLAlchemy 模型)
  ↓
并行组1 (后端 API): T041, T042, T043, T044, T045, T046 (同时执行)
并行组2 (存储服务): T047, T048 (同时执行)
  ↓
并行组3 (前端页面): T049, T050, T051, T052 (依赖组1,同时执行)
```

**时间估算**: 串行 28 小时 → 并行 14 小时 (节省 50%)

### Phase 5 (US3) 并行执行策略
```
串行: T053 (数据库迁移)
  ↓
串行: T054 (SQLAlchemy 模型)
  ↓
并行组1 (后端 API): T055, T056, T057, T058, T059, T060, T061 (同时执行)
并行组2 (监控服务): T062, T063, T068 (同时执行)
  ↓
并行组3 (前端页面): T064, T065, T066, T067 (依赖组1,同时执行)
```

**时间估算**: 串行 32 小时 → 并行 16 小时 (节省 50%)

---

## 任务统计

| Phase | 任务数 | 预估工作量 (人时) | 并行后工作量 (人时) | 优先级 |
|-------|--------|-------------------|---------------------|--------|
| Phase 1: Setup + IaC | 20 | 46 | 28 | 阻塞性 |
| Phase 2: Foundational | 23 | 46 | 23 | 阻塞性 |
| Phase 3: US1 (P1) | 32 | 68 | 37 | Must-Have |
| Phase 4: US2 (P1) | 14 | 28 | 14 | Must-Have |
| Phase 5: US3 (P1) | 19 | 38 | 18 | Must-Have |
| Phase 6: US4 (P2) | 13 | 26 | 15 | Important |
| Phase 7: US5 (P2) | 15 | 30 | 17 | Important |
| Phase 8: Polish + GitOps | 24 | 48 | 29 | 质量保障 |
| **总计** | **160** | **330** | **181** | - |

**MVP 范围 (Phase 1-5)**: 108 个任务, 实际估算:
- **纯开发时间**: 120 人时 (并行后)
- **集成测试和调试**: 48 人时 (40% of 开发时间)
- **代码审查和返工**: 24 人时 (20%)
- **文档编写**: 12 人时 (10%)
- **基础设施部署等待**: 10 人时 (EKS 集群创建、FSx 配置、数据库迁移、验证测试)
- **小计**: 约 214 人时
- **风险缓冲** (20%): 43 人时
- **最终估算**: 约 **257 人时**

**说明**:
- 估算基于并行开发模式（多团队协作）
- 假设基础设施环境稳定（AWS 服务可用性 99.9%+）
- 不含 Phase 6-8 的 P2 功能和质量保障任务

**包含功能**: 项目基础结构、IaC 基础、HyperPod EKS 集群（拆分为 3 个子任务）、HyperPod Add-ons、FSx for Lustre 高性能存储、基础设施验证测试、HyperPod SDK 方法验证（提前执行）及备选方案、训练任务管理、模型版本控制、数据集管理、资源配额、集群监控和审计日志

---

## 验收标准汇总

### 功能需求 (Functional Requirements)
- **FR-001**: 训练任务提交成功率 >95% (Phase 3, T025)
- **FR-002**: 训练任务启动时间 <2分钟 (Phase 3, T036)
- **FR-003**: Gang Scheduling Pod 就绪时间窗口 ≤60秒 (Phase 3, T036a)
- **FR-003b**: 状态同步延迟 <30秒 (Phase 3, T037)
- **FR-006**: 数据集上传速度 ≥100MB/s (Phase 4, T047)
- **FR-007**: 支持 ≥10TB 数据集 (Phase 4, T048)
- **FR-008**: 版本控制支持 ≥100 个版本 (Phase 4, T046)
- **FR-012**: 配额检查延迟 <100ms (Phase 5, T058-T060)
- **FR-013**: 集群监控刷新频率 ≤30秒 (Phase 5, T062)
- **FR-014**: 支持 ≥1000 并发用户 (Phase 5, T064-T065)
- **FR-018**: 报表生成时间 <5秒 (Phase 6, T071-T072)
- **FR-019**: 成本计算准确率 >98% (Phase 6, T069)
- **FR-023**: IDE 启动时间 <3分钟 (Phase 7, T081)
- **FR-024**: 支持 ≥50 并发在线开发环境 (Phase 7, T085)

### 成功标准 (Success Criteria)
- **SC-001**: 支持 PyTorch DDP/FSDP/DeepSpeed ZeRO (Phase 3, T036)
- **SC-002**: 检查点保存成功率 >99% (Phase 3, T038)
- **SC-005**: S3 到 FSx 同步时间 <10分钟 (1TB 数据集) (Phase 4, T048)
- **SC-008**: Prometheus 指标保留期 ≥30天 (Phase 5, T062)
- **SC-012**: 支持 ≥12个月历史数据查询 (Phase 6, T070)
- **SC-015**: 在线开发环境自动保存间隔 ≤5分钟 (Phase 7, T090)

---

## 下一步行动

1. **获取项目批准**: 审核 tasks.md,确认优先级和资源分配
2. **环境准备**: 执行 Phase 1 (Setup) 任务,搭建开发环境
3. **MVP 开发**: 执行 Phase 2-3 (Foundational + US1),实现核心训练任务管理功能
4. **迭代交付**: 按用户故事优先级 (P1 → P2) 逐步交付功能
5. **质量保障**: 执行 Phase 8 (Polish) 任务,确保系统稳定性和可维护性

---

**文档版本**: v1.0
**生成日期**: 2026-01-03
**维护者**: AI Studio 项目团队