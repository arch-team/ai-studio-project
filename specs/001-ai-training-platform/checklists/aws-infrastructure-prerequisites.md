# AWS 基础设施前提条件检查清单

**Purpose**: 验证开发环境所需的 AWS 基础设施服务配置是否满足规范要求，确保项目运行和功能测试的前提条件就绪

**Created**: 2026-01-04
**Checklist Type**: 开发环境准备检查 (配置合规性级别)
**Scope**: 全部基础设施依赖项 (HyperPod EKS + Add-ons + 存储服务 + 安全网络)

---

## A. HyperPod EKS 集群核心组件

### A1. EKS 集群配置
- [ ] CHK001 - 规范是否明确指定 EKS 集群版本要求? [Clarity, Spec §Technical Context "EKS 1.32+"]
- [ ] CHK002 - 规范是否定义 EKS 集群的多可用区部署要求 (高可用性)? [Completeness, Spec §T008c "多可用区部署 (至少 3 个 AZ)"]
- [ ] CHK003 - 规范是否明确 EKS 集群控制平面的冗余配置要求? [Completeness, Spec §T008c]
- [ ] CHK004 - 规范是否定义 EKS Add-ons 版本要求 (EBS CSI Driver, FSx CSI Driver, VPC CNI)? [Clarity, Gap]

### A2. GPU 节点组配置
- [ ] CHK005 - 规范是否明确列出支持的 GPU 实例类型? [Completeness, Spec §T008c "p4d.24xlarge, p5.48xlarge, trn1.32xlarge"]
- [ ] CHK006 - 规范是否定义 GPU 节点组的最小/最大节点数量? [Clarity, Spec §T008c "最小 2 节点,最大 100 节点"]
- [ ] CHK007 - 规范是否说明 GPU 节点组的 Auto Scaling 策略触发条件? [Gap]
- [ ] CHK008 - 规范是否定义 GPU 驱动版本和 CUDA 版本要求? [Gap]

### A3. EFA 高性能网络
- [ ] CHK009 - 规范是否明确 EFA (Elastic Fabric Adapter) 启用要求? [Completeness, Spec §T008c "启用 EFA 高性能网络"]
- [ ] CHK010 - 规范是否定义 EFA 网络带宽要求 (如 400-3200 Gbps)? [Clarity, Spec §Edge Cases "每节点 400-3200 Gbps 带宽"]
- [ ] CHK011 - 规范是否说明 EFA 网络拓扑优化的配置方式? [Completeness, Spec §T008c]

### A4. IAM 角色和权限
- [ ] CHK012 - 规范是否定义 EKS 节点角色的最小权限集? [Completeness, Spec §T008c "遵循最小权限原则"]
- [ ] CHK013 - 规范是否明确 Pod IAM 角色和 Service Account 映射要求? [Completeness, Spec §T008c]
- [ ] CHK014 - 规范是否定义 RBAC 策略的具体配置? [Gap]

---

## B. HyperPod Add-ons 组件

### B1. Training Operator
- [ ] CHK015 - 规范是否明确 HyperPod Training Operator 的安装要求? [Completeness, Spec §T008d]
- [ ] CHK016 - 规范是否定义支持的训练框架 CRD (PyTorchJob, TensorFlowJob)? [Completeness, Spec §T008d "PyTorchJob, TensorFlowJob CRD"]
- [ ] CHK017 - 规范是否说明 Training Operator Webhook 的健康检查端点? [Clarity, Spec §T008d "curl localhost:9443/healthz"]
- [ ] CHK018 - 规范是否定义支持的分布式训练模式配置 (DDP/FSDP/DeepSpeed ZeRO)? [Completeness, Spec §FR-001]

### B2. Task Governance (Kueue)
- [ ] CHK019 - 规范是否明确 Kueue 资源调度器的安装要求? [Completeness, Spec §T008d]
- [ ] CHK020 - 规范是否定义 ClusterQueue 和 LocalQueue 的配置? [Completeness, Spec §T008d]
- [ ] CHK021 - 规范是否明确三级优先级 (PriorityClass) 的映射关系? [Clarity, Spec §T008d "critical/high/medium 映射到 spec.md 的 high/medium/low"]
- [ ] CHK022 - 规范是否定义 Gang Scheduling 的超时时间配置? [Clarity, Spec §FR-003 "60秒超时"]
- [ ] CHK023 - 规范是否说明 Gang Scheduling 重试策略的具体参数? [Completeness, Spec §FR-003 "最大重试次数: 3 次, 指数退避: 30s → 60s → 120s"]
- [ ] CHK024 - 规范是否定义抢占规则和冷却期配置? [Gap]

### B3. Observability Add-on
- [ ] CHK025 - 规范是否明确 Prometheus + Grafana 的部署要求? [Completeness, Spec §T008d]
- [ ] CHK026 - 规范是否定义监控数据采集器 (Node Exporter, cAdvisor, DCGM Exporter)? [Completeness, Spec §T008d]
- [ ] CHK027 - 规范是否说明监控数据保留期要求? [Clarity, Spec §T008d "30 天", FR-007 "15-30天"]
- [ ] CHK028 - 规范是否定义预置 Grafana 仪表盘的内容? [Completeness, Spec §T008d "集群健康、训练任务分布、资源利用率"]
- [ ] CHK029 - 规范是否明确 Prometheus 采集间隔要求? [Clarity, Spec §FR-007 "15 秒"]

### B4. Elastic Agent (Auto-Resume)
- [ ] CHK030 - 规范是否明确 HyperPod Elastic Agent 的配置要求? [Completeness, Spec §T008d]
- [ ] CHK031 - 规范是否定义检查点创建的默认间隔? [Clarity, Spec §T008d "默认 10-15 分钟间隔", FR-010]
- [ ] CHK032 - 规范是否说明 Auto-Resume 策略的触发条件? [Completeness, Spec §T008d "节点故障自动恢复"]
- [ ] CHK033 - 规范是否定义节点故障检测阈值? [Clarity, Spec §T008d "PodsReady=False 持续 >30 秒"]
- [ ] CHK034 - 规范是否说明 Deep Health Check 的配置要求? [Gap]

### B5. Spaces Add-on (JupyterLab/VS Code)
- [ ] CHK035 - 规范是否明确 SageMaker Spaces Add-on 的安装要求? [Completeness, Spec §T008d]
- [ ] CHK036 - 规范是否定义支持的 IDE 镜像类型? [Completeness, Spec §T008d "Data Science, PyTorch, TensorFlow"]
- [ ] CHK037 - 规范是否说明 IDE 实例类型限制? [Clarity, Spec §User Story 5 "ml.g5.xlarge, ml.g5.2xlarge"]
- [ ] CHK038 - 规范是否定义 EFS 持久化存储的挂载配置? [Completeness, Spec §T008d]
- [ ] CHK039 - 规范是否明确自动保存间隔要求? [Clarity, Spec §T008d "JupyterLab 120 秒, VS Code 1 秒"]
- [ ] CHK040 - 规范是否定义 Space 启动时间目标? [Clarity, Spec §User Story 5 "3分钟内"]

---

## C. 存储服务

### C1. Aurora MySQL 数据库
- [ ] CHK041 - 规范是否明确 Aurora MySQL 版本要求? [Clarity, Spec §Technical Context "Aurora MySQL 3.04.x (生产环境,兼容 MySQL 8.0)"]
- [ ] CHK042 - 规范是否定义开发环境数据库配置 (本地 MySQL)? [Clarity, Spec §Technical Context "MySQL 8.0.28 (开发环境本地部署)"]
- [ ] CHK043 - 规范是否说明 Aurora Serverless v2 的配置要求? [Gap]
- [ ] CHK044 - 规范是否定义数据库自动备份策略? [Gap]
- [ ] CHK045 - 规范是否明确数据库连接池配置要求? [Gap]

### C2. FSx for Lustre 高性能存储
- [ ] CHK046 - 规范是否明确 FSx for Lustre 的吞吐量要求? [Clarity, Spec §Technical Context "≥5GB/s 单客户端吞吐量"]
- [ ] CHK047 - 规范是否定义 FSx 部署类型 (Persistent_2)? [Completeness, Spec §T008e "Persistent_2 部署类型"]
- [ ] CHK048 - 规范是否说明 FSx 初始容量和最大容量? [Clarity, Spec §T008e "初始 ≥10 TiB, 最大 100 TiB"]
- [ ] CHK049 - 规范是否定义 S3 Data Repository Association 配置? [Completeness, Spec §T008e]
- [ ] CHK050 - 规范是否明确 AutoImportPolicy 事件类型? [Clarity, Spec §T008e "NEW/CHANGED/DELETED"]
- [ ] CHK051 - 规范是否定义 FSx CSI Driver 的 StorageClass 配置? [Completeness, Spec §T008e]
- [ ] CHK052 - 规范是否说明存储容量自动扩容的触发条件? [Clarity, Spec §T008e "使用率 >80% 触发扩容"]

### C3. S3 存储桶
- [ ] CHK053 - 规范是否明确 S3 存储桶的用途分类 (数据集、模型、检查点)? [Completeness, Spec §T008b]
- [ ] CHK054 - 规范是否定义 S3 版本控制启用要求? [Completeness, Spec §T008b "启用版本控制"]
- [ ] CHK055 - 规范是否说明 S3 生命周期策略? [Completeness, Spec §T008b "生命周期策略", FR-011 "30 天前的冷检查点"]
- [ ] CHK056 - 规范是否明确 S3 SSE-KMS 加密配置要求? [Completeness, Spec §FR-018 "S3 SSE-KMS"]

### C4. 分层检查点存储
- [ ] CHK057 - 规范是否明确三层存储架构 (NVMe → FSx → S3)? [Completeness, Spec §FR-011]
- [ ] CHK058 - 规范是否定义热/温/冷检查点的分层规则? [Clarity, Spec §FR-011 "最近 3 个 NVMe, 第 4-10 个 FSx, >10 或 >72h S3"]
- [ ] CHK059 - 规范是否说明迁移触发机制? [Completeness, Spec §FR-011 "主触发: 检查点创建后 10 分钟内, 兜底: 每 30 分钟扫描"]
- [ ] CHK060 - 规范是否定义存储满载时的应对策略? [Completeness, Spec §FR-011 "保留最近 1 个检查点,暂停新检查点创建"]
- [ ] CHK061 - 规范是否说明检查点完整性校验机制? [Completeness, Spec §FR-011 "SHA-256 校验和"]

---

## D. 安全和网络服务

### D1. VPC 网络配置
- [ ] CHK062 - 规范是否明确 VPC 子网规划 (公有/私有子网)? [Gap]
- [ ] CHK063 - 规范是否定义 NAT Gateway 配置? [Completeness, Spec §T008b "NAT Gateway"]
- [ ] CHK064 - 规范是否说明 Security Group 规则? [Completeness, Spec §T008c "训练任务端口、Kubernetes API 端口、EFA 网络端口"]
- [ ] CHK065 - 规范是否定义 FSx 访问所需的端口? [Clarity, Spec §T008e "端口 988, 1021-1023"]
- [ ] CHK066 - 规范是否说明 PrivateLink 端点配置 (S3, CloudWatch)? [Gap]

### D2. IAM 和身份认证
- [ ] CHK067 - 规范是否明确 IAM Identity Center (SSO) 集成要求? [Completeness, Spec §FR-015 "企业 SSO (SAML/OIDC)"]
- [ ] CHK068 - 规范是否定义本地账号备用认证机制? [Completeness, Spec §FR-015 "本地账号备用"]
- [ ] CHK069 - 规范是否说明 SSO 故障转移机制? [Completeness, Spec §FR-015 "超时阈值 5 秒, 连续失败 3 次"]
- [ ] CHK070 - 规范是否定义 RBAC 角色层次? [Clarity, Spec §T013b "admin/project_manager/engineer/viewer"]
- [ ] CHK071 - 规范是否说明密码安全策略 (本地账号)? [Completeness, Spec §T013c "最小 12 字符, bcrypt/argon2id"]

### D3. 数据加密
- [ ] CHK072 - 规范是否明确静态数据加密要求? [Completeness, Spec §FR-018 "S3 SSE-KMS"]
- [ ] CHK073 - 规范是否定义传输层加密要求? [Clarity, Spec §FR-018 "TLS 1.2 或更高版本"]
- [ ] CHK074 - 规范是否说明 KMS 密钥管理策略? [Gap]

### D4. 网络隔离和 QoS
- [ ] CHK075 - 规范是否明确 Kubernetes NetworkPolicy 配置要求? [Completeness, Spec §FR-021, T008f]
- [ ] CHK076 - 规范是否定义 Pod 级网络隔离策略? [Completeness, Spec §T008f "默认拒绝策略"]
- [ ] CHK077 - 规范是否说明训练任务网络 QoS 配置? [Completeness, Spec §T008f "QoS Class: Guaranteed"]
- [ ] CHK078 - 规范是否定义网络性能目标? [Clarity, Spec §FR-021 "网络延迟 P99 <10ms, 带宽利用率 >80%"]

### D5. 审计和合规
- [ ] CHK079 - 规范是否明确审计日志保留期要求? [Clarity, Spec §FR-017 "≥90 天"]
- [ ] CHK080 - 规范是否定义 CloudWatch Logs 日志组配置? [Completeness, Spec §FR-017 "/ai-platform/audit-logs"]
- [ ] CHK081 - 规范是否说明 AWS CloudTrail 集成范围? [Completeness, Spec §FR-017 "IAM, S3, EKS, SageMaker HyperPod API"]
- [ ] CHK082 - 规范是否定义应用层审计日志字段结构? [Completeness, Spec §FR-017 "JSON 格式,包含 timestamp/user_id/operation_type 等"]

---

## E. 基础设施验证和 SDK

### E1. 基础设施验证测试
- [ ] CHK083 - 规范是否定义集群健康检查的验证项? [Completeness, Spec §T008g "kubectl cluster-info, 节点 Ready 状态"]
- [ ] CHK084 - 规范是否说明 GPU 节点验证的具体测试? [Completeness, Spec §T008g "nvidia-smi 测试 Pod"]
- [ ] CHK085 - 规范是否定义 FSx 存储性能验证标准? [Clarity, Spec §T008e "fio 工具验证单客户端吞吐量 ≥5GB/s"]
- [ ] CHK086 - 规范是否说明网络连通性测试范围? [Completeness, Spec §T008g "Pod 到 Internet, PrivateLink, EFA"]

### E2. HyperPod SDK 依赖
- [ ] CHK087 - 规范是否明确 `sagemaker-hyperpod` SDK 的使用范围? [Completeness, Spec §Constitution "Cluster/Training/Inference/Space 四大功能模块"]
- [ ] CHK088 - 规范是否定义 SDK 方法验证的要求? [Completeness, Spec §T008h "Training/Space/Cluster 模块方法签名"]
- [ ] CHK089 - 规范是否说明 SDK 不支持时的备选方案? [Completeness, Spec §FR-001 "MAY 使用 boto3 或 kubernetes-client"]
- [ ] CHK090 - 规范是否定义 SDK 绕过的例外申请流程? [Clarity, Spec §FR-001 "MUST 提交例外申请并获得平台治理委员会批准"]

---

## F. 开发环境特定配置

### F1. 本地开发环境
- [ ] CHK091 - 规范是否定义本地 MySQL 容器配置? [Completeness, Spec §T003 "MySQL 8.0.28, 端口 3306"]
- [ ] CHK092 - 规范是否说明必需的环境变量? [Completeness, Spec §T006 "DATABASE_URL, AWS_REGION, HYPERPOD_CLUSTER_ARN"]
- [ ] CHK093 - 规范是否定义 Python 版本要求? [Clarity, Spec §Technical Context "Python 3.11"]
- [ ] CHK094 - 规范是否说明后端依赖包版本? [Completeness, Spec §T004 "fastapi==0.109.0, sqlalchemy==2.0+, pydantic==2.0+"]
- [ ] CHK095 - 规范是否定义前端 Node.js/npm 版本要求? [Gap]

### F2. AWS 凭证和访问
- [ ] CHK096 - 规范是否说明开发环境所需的 AWS 凭证配置方式? [Gap]
- [ ] CHK097 - 规范是否定义开发者所需的最小 IAM 权限? [Gap]
- [ ] CHK098 - 规范是否说明如何访问共享开发 HyperPod 集群? [Gap]

---

## 检查清单统计

| 类别 | 检查项数量 | 完整性 | 清晰性 | 一致性 | 缺失项 |
|------|-----------|--------|--------|--------|--------|
| A. HyperPod EKS 核心 | 14 | 10 | 3 | 0 | 1 |
| B. HyperPod Add-ons | 26 | 16 | 8 | 0 | 2 |
| C. 存储服务 | 21 | 13 | 6 | 0 | 2 |
| D. 安全和网络 | 21 | 12 | 5 | 0 | 4 |
| E. 验证和 SDK | 8 | 6 | 2 | 0 | 0 |
| F. 开发环境配置 | 8 | 4 | 1 | 0 | 3 |
| **总计** | **98** | **61** | **25** | **0** | **12** |

---

## 关键发现摘要

### 规范完整性较好的领域
- HyperPod Add-ons 配置 (Training Operator, Kueue, Observability)
- 分布式训练模式支持 (DDP/FSDP/DeepSpeed ZeRO)
- 检查点管理和分层存储策略
- 审计日志和安全合规要求

### 需要补充澄清的领域 [Gap]
- **CHK004**: EKS Add-ons 具体版本要求未明确
- **CHK007**: GPU 节点组 Auto Scaling 策略触发条件
- **CHK008**: GPU 驱动和 CUDA 版本要求
- **CHK024**: Kueue 抢占规则和冷却期配置
- **CHK034**: Deep Health Check 配置要求
- **CHK043-045**: Aurora MySQL Serverless v2 和备份策略
- **CHK062, CHK066**: VPC 子网规划和 PrivateLink 端点
- **CHK074**: KMS 密钥管理策略
- **CHK095-098**: 开发环境 Node.js 版本和 AWS 凭证配置

---

## 使用说明

1. **逐项检查**: 按照检查项顺序验证规范文档是否满足要求
2. **标记状态**:
   - ✅ 规范已明确定义且配置正确
   - ⚠️ 规范已定义但需要确认配置
   - ❌ 规范缺失或配置不符合要求
3. **记录问题**: 对于 ❌ 项，记录具体问题和建议的修复方案
4. **更新规范**: 针对 [Gap] 标记的项，考虑是否需要补充规范定义
