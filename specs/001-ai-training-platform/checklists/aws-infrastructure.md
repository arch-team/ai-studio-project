# AWS 基础设施依赖项质量检查清单: 企业级AI训练平台

**Purpose**: 验证 tasks.md 中 AWS 基础设施创建任务的完整性,确保后续开发、测试验证工作所需的 SageMaker HyperPod with EKS 等基础设施任务已明确定义
**Created**: 2026-01-04
**Updated**: 2026-01-04 (针对 tasks.md 基础设施任务覆盖性检查)
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [tasks.md](../tasks.md)

**检查原则**: 本检查清单测试需求文档本身的质量,而非实施结果。每个检查项验证需求是否完整、明确、一致且可实施。

---

## 🚨 关键发现: tasks.md 基础设施任务覆盖性分析

### 已有的基础设施任务 (Phase 1: T008a/T008b)
| 任务ID | 内容 | 覆盖范围 |
|--------|------|----------|
| T008a | AWS CDK 项目结构 | CDK 初始化、多环境配置 |
| T008b | AWS CDK 核心 Stacks | VPC、RDS Aurora MySQL、S3、IAM Roles |

### 🔴 关键缺失: HyperPod EKS 基础设施任务
根据 plan.md 约束: **"Requires AWS SageMaker HyperPod with EKS infrastructure"**

以下基础设施任务 **尚未在 tasks.md 中定义**:
1. ❌ SageMaker HyperPod EKS 集群创建
2. ❌ HyperPod Training Operator 安装
3. ❌ HyperPod Task Governance (Kueue) 配置
4. ❌ HyperPod Observability Add-on 部署
5. ❌ HyperPod Elastic Agent 配置
6. ❌ Amazon SageMaker Spaces Add-on 安装
7. ❌ Amazon FSx for Lustre 文件系统创建
8. ❌ EFA 高性能网络配置
9. ❌ GPU 节点组配置

---

## HyperPod 组件依赖完整性

- [ ] CHK001 - 是否明确列出了所有必需的 HyperPod 核心组件及其职责?(HyperPod Training Operator、Task Governance/Kueue、Observability Add-on、Elastic Agent、Spaces Add-on) [Completeness, Spec §Technical Context + FR-001/FR-003/FR-004/FR-010/FR-012]
- [ ] CHK002 - 是否定义了 HyperPod Training Operator 支持的训练框架和模式配置要求?(PyTorch, DDP/FSDP/DeepSpeed ZeRO) [Completeness, Spec §FR-001]
- [ ] CHK003 - 是否明确 HyperPod Task Governance (Kueue) 的优先级配置和抢占规则?(三级优先级映射到 Kueue PriorityClass: critical/high/medium) [Clarity, Spec §FR-004]
- [ ] CHK004 - 是否定义了 HyperPod Elastic Agent 的检查点管理和 Auto-Resume 配置参数?(检查点间隔、存储路径、恢复策略) [Completeness, Spec §FR-010]
- [ ] CHK005 - 是否明确 HyperPod Observability Add-on (Prometheus + Grafana) 的监控指标收集范围和查询接口?(训练指标、资源利用率、日志流) [Completeness, Spec §FR-007 + FR-016]
- [ ] CHK006 - 是否定义了 Amazon SageMaker Spaces Add-on 的 Space 生命周期管理要求?(创建、配置、资源分配、删除) [Completeness, Spec §FR-012]
- [ ] CHK007 - 是否明确了 HyperPod Health Check Agent 的健康检查策略和故障检测阈值?(Deep Health Check、节点故障检测) [Clarity, Spec §FR-016]
- [ ] CHK008 - HyperPod 组件版本兼容性需求是否已定义?(EKS 版本、HyperPod API 版本、SDK 版本) [Gap, Spec §Technical Context]

## EKS 集群配置需求

- [ ] CHK009 - 是否明确了 EKS 集群的最低版本要求和升级策略?(EKS 1.32+) [Clarity, Spec §Technical Context]
- [ ] CHK010 - 是否定义了 EKS 节点组的实例类型和资源规格要求?(GPU 实例类型、CPU/内存配置) [Gap]
- [ ] CHK011 - 是否明确了 EKS Add-ons 的依赖项和版本要求?(EBS CSI Driver、FSx CSI Driver、VPC CNI) [Gap]
- [ ] CHK012 - 是否定义了 EKS 集群的扩缩容策略和节点数量限制?(最小/最大节点数、Auto Scaling Group 配置) [Gap]
- [ ] CHK013 - 是否明确了 EKS 集群的 IAM 角色和权限边界配置要求?(节点角色、Pod IAM、Service Account 映射) [Completeness, Spec §FR-015]
- [ ] CHK014 - 是否定义了 EKS 集群的高可用性配置?(多可用区部署、控制平面冗余) [Gap]
- [ ] CHK015 - 是否明确了 Kubernetes RBAC 与平台用户角色的映射关系?(用户角色 → K8S ServiceAccount → RBAC Policy) [Clarity, Spec §FR-015]
- [ ] CHK016 - 是否定义了 Gang Scheduling 的超时时间和失败处理策略?(默认 60 秒是否可配置?超时后的重试机制?) [Clarity, Spec §FR-003]

## 存储系统设计需求

- [ ] CHK017 - 是否明确了 Amazon FSx for Lustre 的容量和吞吐量规格要求?(单客户端吞吐量 ≥5GB/s,总容量) [Clarity, Spec §Technical Context + FR-007]
- [ ] CHK018 - 是否定义了 FSx for Lustre 与 EKS 的挂载方式和 CSI Driver 配置?(PersistentVolume 配置、StorageClass 参数) [Gap]
- [ ] CHK019 - 是否明确了 S3 存储桶的生命周期策略和访问权限配置?(模型制品、冷检查点归档、30 天保留策略) [Completeness, Spec §FR-011 + FR-018]
- [ ] CHK020 - 是否定义了分层检查点存储的迁移触发条件和时间窗口?(NVMe → FSx 迁移阈值、FSx → S3 迁移时间) [Clarity, Spec §FR-011]
- [ ] CHK021 - 是否明确了 NVMe 本地存储的容量规划和清理策略?(热检查点保留数量、存储满载处理) [Completeness, Spec §FR-011]
- [ ] CHK022 - 是否定义了检查点完整性验证机制的技术实现细节?(SHA-256 校验和计算时机、验证流程) [Clarity, Spec §FR-011]
- [ ] CHK023 - 是否明确了数据集上传的断点续传实现方案?(S3 Multipart Upload、进度追踪) [Gap, Spec §FR-005]
- [ ] CHK024 - 是否定义了存储容量告警阈值和自动扩容策略?(剩余空间 <10% 触发告警、扩容决策逻辑) [Completeness, Spec §FR-020]

## 网络架构需求

- [ ] CHK025 - 是否明确了 VPC 网络拓扑和子网划分方案?(公有子网、私有子网、隔离子网) [Gap]
- [ ] CHK026 - 是否定义了 AWS PrivateLink 的服务终端节点列表和配置要求?(S3、SageMaker、CloudWatch 等服务终端节点) [Gap, Spec §Constitution Check]
- [ ] CHK027 - 是否明确了 EFA (Elastic Fabric Adapter) 网络的配置要求和性能目标?(每节点带宽 400-3200 Gbps、网络延迟 P99 <10ms) [Clarity, Spec §FR-021]
- [ ] CHK028 - 是否定义了 Kubernetes NetworkPolicy 的隔离策略和 QoS 配置?(Pod 级网络命名空间隔离、带宽限制) [Completeness, Spec §FR-021]
- [ ] CHK029 - 是否明确了负载均衡器的类型和配置要求?(Application Load Balancer、Network Load Balancer、Ingress Controller) [Gap]
- [ ] CHK030 - 是否定义了外部访问的入口策略和 TLS 终止配置?(API Gateway、TLS 1.2+ 证书管理) [Completeness, Spec §FR-018]
- [ ] CHK031 - 是否明确了 DNS 解析策略和服务发现机制?(内部 DNS、ExternalDNS、Service Mesh) [Gap]

## 安全与合规需求

- [ ] CHK032 - 是否明确了 KMS 加密密钥的管理策略和轮换周期?(S3 SSE-KMS、密钥权限配置) [Clarity, Spec §FR-018]
- [ ] CHK033 - 是否定义了 IAM 权限的最小权限原则实施细节?(Role-Based Access Control、权限边界) [Completeness, Spec §FR-015]
- [ ] CHK034 - 是否明确了企业 SSO 集成的技术方案和身份提供商配置?(SAML/OIDC、IdP 元数据、属性映射) [Clarity, Spec §FR-015]
- [ ] CHK035 - 是否定义了审计日志的存储方案和保留策略?(CloudWatch Logs、S3 归档、90 天保留期) [Completeness, Spec §FR-017]
- [ ] CHK036 - 是否明确了 TLS 证书的获取方式和自动续期机制?(AWS Certificate Manager、Let's Encrypt、cert-manager) [Gap, Spec §FR-018]
- [ ] CHK037 - 是否定义了网络安全组(Security Group)和 NACL 的配置规则?(入站/出站规则、端口开放策略) [Gap]
- [ ] CHK038 - 是否明确了容器镜像的安全扫描和签名验证要求?(ECR 镜像扫描、镜像签名策略) [Gap]
- [ ] CHK039 - 是否定义了敏感数据的脱敏和加密传输策略?(训练数据、日志中的敏感信息处理) [Clarity, Spec §FR-014 备注]

## 可观测性需求

- [ ] CHK040 - 是否明确了 Prometheus 指标的采集配置和存储策略?(指标保留期、采样间隔、远程存储) [Gap, Spec §FR-007]
- [ ] CHK041 - 是否定义了 Amazon Managed Grafana 的仪表盘配置和访问权限?(预定义仪表盘、用户权限映射) [Gap, Spec §FR-016]
- [ ] CHK042 - 是否明确了自定义训练指标的上报机制和性能要求?(Prometheus Pushgateway 地址、上报频率、批量 API) [Completeness, Spec §FR-007 备注]
- [ ] CHK043 - 是否定义了 CloudWatch Logs 的日志流设计和查询性能目标?(日志分组、保留期 30 天、查询响应 P99 <3 秒) [Completeness, Spec §FR-014 + FR-007]
- [ ] CHK044 - 是否明确了 MLflow 实验管理的部署方案和存储后端配置?(SageMaker Managed MLflow、Tracking Server 地址) [Gap, Spec §Constitution Check]
- [ ] CHK045 - 是否定义了告警规则的触发条件和通知渠道?(集群资源告警、训练任务停滞告警、SNS/邮件通知) [Completeness, Spec §FR-016 + FR-022]
- [ ] CHK046 - 是否明确了分布式链路追踪的技术方案?(X-Ray、OpenTelemetry、Jaeger) [Gap]

## 成本管理需求

- [ ] CHK047 - 是否明确了资源配额的计费规则和成本归属逻辑?(按分钟计费、GPU 小时成本单价) [Clarity, Spec §FR-009]
- [ ] CHK048 - 是否定义了预算预警的阈值配置和通知机制?(80%/90%/100% 多级预警、自动限制措施) [Completeness, Spec §FR-009 + User Story 4]
- [ ] CHK049 - 是否明确了存储成本的分层策略和归档规则?(FSx vs S3 成本对比、冷检查点归档节省) [Clarity, Spec §FR-011]
- [ ] CHK050 - 是否定义了资源利用率的优化目标和监控指标?(GPU 集群利用率 ≥70%、成本降低 ≥30%) [Completeness, Spec §SC-001 + SC-006]
- [ ] CHK051 - 是否明确了 Spot 实例或 Savings Plans 的使用策略?(是否允许使用、风险评估) [Gap]

## GitOps 和 IaC 需求

- [ ] CHK052 - 是否明确了 AWS CDK Stack 的划分和依赖关系?(HyperPod Stack、Database Stack、Storage Stack、Network Stack) [Completeness, Spec §Project Structure]
- [ ] CHK053 - 是否定义了 ArgoCD 的配置同步策略和自动部署规则?(Git 仓库结构、同步频率、自动/手动同步) [Clarity, Spec §FR-025]
- [ ] CHK054 - 是否明确了 Helm Charts 的版本管理和依赖配置?(Chart Repository、values.yaml 管理策略) [Gap, Spec §Project Structure]
- [ ] CHK055 - 是否定义了 IaC 代码的审核流程和自动化测试要求?(Pull Request 审核、Terraform Plan 验证) [Completeness, Spec §FR-025]
- [ ] CHK056 - 是否明确了配置漂移检测和修复机制?(ArgoCD 同步状态监控、自动修正策略) [Completeness, Spec §Constitution Check]

## 性能约束和可用性需求

- [ ] CHK057 - 是否明确了 API 响应时间的性能目标和测试方法?(P99 <3 秒、负载测试场景) [Completeness, Spec §SC-007 + Technical Context]
- [ ] CHK058 - 是否定义了训练指标刷新和日志流的性能要求?(指标刷新 ≤30 秒、日志延迟 <10 秒) [Completeness, Spec §FR-007]
- [ ] CHK059 - 是否明确了节点故障恢复的时间目标和实现机制?(5 分钟内自动恢复、Health Check Agent + Auto-Resume) [Completeness, Spec §SC-004 + FR-010]
- [ ] CHK060 - 是否定义了平台可用性的计算方式和监控指标?(年度可用性 99%、SLA 定义) [Clarity, Spec §SC-003]
- [ ] CHK061 - 是否明确了并发用户数的支持目标和性能测试计划?(≥1000 并发用户、压力测试场景) [Completeness, Spec §SC-007]
- [ ] CHK062 - 是否定义了数据集上传的成功率目标和失败重试策略?(99% 成功率、断点续传机制) [Completeness, Spec §SC-008 + FR-005]

## 依赖关系和集成点

- [ ] CHK063 - 是否明确了 `sagemaker-hyperpod` SDK 的版本要求和功能边界?(Cluster/Training/Inference/Space 四大模块的适用范围) [Clarity, Spec §Constitution Check]
- [ ] CHK064 - 是否定义了 boto3 SDK 的使用场景和 API 调用要求?(CloudWatch Metrics/Logs、SageMaker Model Registry、S3) [Completeness, Spec §Constitution Check]
- [ ] CHK065 - 是否明确了 kubernetes-client 的使用场景和限制?(仅用于 Kueue Workload 状态查询、NetworkPolicy 配置) [Completeness, Spec §Constitution Check]
- [ ] CHK066 - 是否定义了 HyperPod 与外部系统的集成点和数据流向?(企业 SSO、外部数据源、第三方监控) [Gap]
- [ ] CHK067 - 是否明确了 Aurora MySQL 与 EKS 的网络连接方式?(VPC Peering、PrivateLink、Security Group 配置) [Gap, Spec §Technical Context]
- [ ] CHK068 - 是否定义了 SageMaker Model Registry 的访问方式和权限配置?(IAM 权限、VPC Endpoint) [Gap, Spec §FR-013]

## 边缘场景和异常处理

- [ ] CHK069 - 是否定义了 HyperPod 集群完全耗尽资源时的处理策略?(高优先级任务排队、用户通知机制) [Gap, Spec §Edge Cases]
- [ ] CHK070 - 是否明确了存储满载时的紧急迁移和告警机制?(NVMe/FSx 使用率 >90% 触发紧急迁移) [Completeness, Spec §FR-011]
- [ ] CHK071 - 是否定义了检查点迁移失败的回退和重试策略?(保留原位置检查点、最多 3 次重试) [Completeness, Spec §FR-011]
- [ ] CHK072 - 是否明确了单个节点网络中断但未完全故障时的响应机制?(部分 Pod NotReady、训练任务状态转换) [Gap, Spec §Edge Cases]
- [ ] CHK073 - 是否定义了连续抢占失败超过阈值时的处理策略?(preemption_count ≥3 次转 Failed 状态) [Completeness, Spec §Training Job State Model]
- [ ] CHK074 - 是否明确了训练任务停滞检测的触发条件和告警机制?(30 分钟内指标变化率 <0.1%、可禁用检测) [Completeness, Spec §FR-022]

## 文档和可追溯性

- [ ] CHK075 - 是否明确了 AWS 官方文档的参考链接和版本对齐?(SageMaker HyperPod Documentation、EKS Best Practices) [Traceability, Spec §FR-003 备注]
- [ ] CHK076 - 是否定义了基础设施配置的文档化要求和更新流程?(IaC 代码注释、README、变更日志) [Gap]
- [ ] CHK077 - 是否明确了监控指标和告警规则的命名规范和文档?(Prometheus 指标命名、告警规则定义) [Gap]
- [ ] CHK078 - 是否定义了基础设施变更的审批流程和影响评估机制?(变更管理、影响范围分析) [Gap]

---

## 检查清单使用说明

1. **完成标记**: 使用 `[x]` 标记已通过检查的项目
2. **问题记录**: 在检查项下方添加评论说明发现的问题或需要澄清的内容
3. **优先级**: 标记为 `[Gap]` 的项目表示需求文档中缺失的内容,应优先补充
4. **追溯性**: 每个检查项包含 `[Spec §XX]` 引用,便于定位到规范文档的对应章节
5. **协作**: 多人协作时可在检查项后添加审核人和审核日期

## 检查结果汇总

**总计**: 78 个检查项

**按类别统计**:
- HyperPod 组件依赖: 8 项
- EKS 集群配置: 8 项
- 存储系统设计: 8 项
- 网络架构: 7 项
- 安全与合规: 8 项
- 可观测性: 7 项
- 成本管理: 5 项
- GitOps 和 IaC: 5 项
- 性能约束和可用性: 6 项
- 依赖关系和集成点: 6 项
- 边缘场景和异常处理: 6 项
- 文档和可追溯性: 4 项

**完成率**: 0/78 (0%)

**建议优先处理**: 标记为 `[Gap]` 的 28 项缺失需求,这些是规范文档中尚未明确定义的关键基础设施依赖项。

---

## 🎯 tasks.md 基础设施任务覆盖性检查 (新增)

> **本节专门验证 tasks.md 是否包含保证后续开发、测试验证工作顺利进行所需的 AWS 基础设施创建任务**

### HyperPod EKS 集群创建任务

- [ ] CHK-TASK-001 - tasks.md 是否定义了 SageMaker HyperPod EKS 集群创建任务? [Gap, Critical - plan.md Constraints: "Requires AWS SageMaker HyperPod with EKS infrastructure", 后续 T036/T037/T038 均依赖此集群]
- [ ] CHK-TASK-002 - tasks.md 是否定义了 EKS 集群版本要求和节点组配置任务? [Gap, plan.md: "EKS 1.32+"]
- [ ] CHK-TASK-003 - tasks.md 是否定义了 GPU 实例类型节点组创建任务? (p4d.24xlarge, p5.48xlarge, trn1.32xlarge) [Gap, spec.md FR-001]

### HyperPod Add-ons 安装任务

- [ ] CHK-TASK-004 - tasks.md 是否定义了 HyperPod Training Operator 安装和配置任务? [Gap, plan.md Technical Context, T036 "HyperPodPytorchJob 集成逻辑" 前置依赖]
- [ ] CHK-TASK-005 - tasks.md 是否定义了 HyperPod Task Governance (Kueue) 安装和 ClusterQueue/LocalQueue 配置任务? [Gap, spec.md FR-004 三级优先级调度, T014 前置依赖]
- [ ] CHK-TASK-006 - tasks.md 是否定义了 HyperPod Observability Add-on (Prometheus + Grafana) 部署任务? [Gap, spec.md FR-007/FR-016, T062/T063 前置依赖]
- [ ] CHK-TASK-007 - tasks.md 是否定义了 HyperPod Elastic Agent 配置任务? (检查点管理、Auto-Resume) [Gap, spec.md FR-010/FR-011]
- [ ] CHK-TASK-008 - tasks.md 是否定义了 Amazon SageMaker Spaces Add-on 安装任务? [Gap, spec.md FR-012, T085 前置依赖]

### 存储基础设施创建任务

- [ ] CHK-TASK-009 - tasks.md 是否定义了 Amazon FSx for Lustre 文件系统创建任务? (≥5GB/s 吞吐量) [Gap, spec.md FR-007, T048 "FSx for Lustre 路径管理" 前置依赖]
- [ ] CHK-TASK-010 - tasks.md 是否定义了 FSx for Lustre CSI Driver 安装和 StorageClass 配置任务? [Gap]
- [ ] CHK-TASK-011 - tasks.md 是否定义了 S3 存储桶 SSE-KMS 加密配置验证任务? [Partial, T015a 定义但需与 T008b 协调确保一致性]

### 网络基础设施配置任务

- [ ] CHK-TASK-012 - tasks.md 是否定义了 EFA (Elastic Fabric Adapter) 网络配置任务? [Gap, spec.md Edge Cases "EFA高性能网络拓扑"]
- [ ] CHK-TASK-013 - tasks.md 是否定义了 AWS PrivateLink 端点创建任务? (S3, CloudWatch, SageMaker) [Gap, plan.md Constitution Check "VPC 隔离...使用 PrivateLink 访问 AWS 服务"]
- [ ] CHK-TASK-014 - tasks.md 是否定义了 Kubernetes NetworkPolicy 网络隔离配置任务? [Gap, spec.md FR-021]

### 任务依赖链完整性

- [ ] CHK-TASK-015 - tasks.md Phase 1 (Setup) 中的 T008b 是否明确包含 HyperPod EKS 集群 Stack 定义? [Gap, 当前 T008b 仅包含 VPC/RDS/S3/IAM,未提及 EKS/HyperPod]
- [ ] CHK-TASK-016 - Phase 3 (US1) 的 T036 "HyperPodPytorchJob 集成逻辑" 是否标注对 HyperPod 集群的前置依赖? [Consistency, 当前未明确标注依赖]
- [ ] CHK-TASK-017 - Phase 5 (US3) 的 T062 "Prometheus 指标采集集成" 是否标注对 Observability Add-on 的前置依赖? [Consistency, 当前未明确标注依赖]
- [ ] CHK-TASK-018 - Phase 7 (US5) 的 T085 "SageMaker Spaces 集成" 是否标注对 Spaces Add-on 的前置依赖? [Consistency, 当前未明确标注依赖]

### 基础设施验证和测试任务

- [ ] CHK-TASK-019 - tasks.md 是否定义了 HyperPod 集群健康检查和冒烟测试任务? [Gap, 确保基础设施就绪后方可进入 Phase 2+]
- [ ] CHK-TASK-020 - tasks.md 是否定义了 GPU 节点可用性验证任务? (nvidia-smi 测试) [Gap]
- [ ] CHK-TASK-021 - tasks.md 是否定义了存储挂载点验证任务? (FSx mount 测试) [Gap]

---

## 📋 建议的新增任务清单

基于上述检查,建议在 tasks.md 的 **Phase 1 (Setup)** 中新增以下任务:

```markdown
### HyperPod EKS 基础设施 (建议新增)
- [ ] [T008c] [P] HyperPod EKS 集群 Stack - 编写 AWS CDK Stack 创建 SageMaker HyperPod with EKS 集群,配置 EKS 1.32+ 版本,GPU 节点组 (p4d.24xlarge),EFA 网络支持
- [ ] [T008d] [P] HyperPod Add-ons 配置 - 安装和配置 HyperPod Training Operator、Task Governance (Kueue)、Observability Add-on (Prometheus + Grafana)、Elastic Agent、Spaces Add-on
- [ ] [T008e] FSx for Lustre Stack - 创建 Amazon FSx for Lustre 文件系统 (≥5GB/s 吞吐量),配置 S3 Data Repository Association,安装 FSx CSI Driver
- [ ] [T008f] PrivateLink 端点配置 - 创建 VPC Endpoints (S3 Gateway、CloudWatch Logs、SageMaker API 等),确保私有网络访问 AWS 服务
- [ ] [T008g] HyperPod 集群验证测试 - 执行集群健康检查 (节点状态、GPU 可用性、网络连通性),验证 Add-ons 正常运行,生成验证报告
```

**依赖关系**: T008a → T008b → T008c → T008d/T008e/T008f (可并行) → T008g

---

## 检查执行建议

1. **立即行动**: 补充 HyperPod EKS 基础设施创建任务 (CHK-TASK-001 ~ CHK-TASK-008)
2. **验证依赖链**: 更新 Phase 3-7 任务的依赖关系,明确标注对基础设施的前置依赖
3. **添加验证任务**: 增加基础设施就绪验证任务作为 Phase 2 的入口门控
