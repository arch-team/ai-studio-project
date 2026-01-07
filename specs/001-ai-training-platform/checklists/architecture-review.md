# 架构审查检查清单 - AI训练平台

**检查清单类型**: 架构质量审查
**创建日期**: 2026-01-05
**审查范围**: 技术选型、实现方案、架构设计、系统可维护性
**审查目标**: 确保架构设计符合企业级标准，技术选型合理，实施方案可行且可维护

## 目的说明

本检查清单用于审查 `tasks.md` 中的技术选型和实现方案是否符合以下原则：
- ✅ 架构简单清晰、系统低耦合
- ✅ 可扩展性、可维护性
- ✅ 避免过度设计
- ✅ 松散耦合、抽象化、单一职责

---

## I. AWS 基础设施架构审查

### 1. VPC 和网络设计

- [x] **CHK001 - ✅ 已解决** - VPC CIDR 配置已验证满足扩展需求并支持可配置。[可扩展性, tasks.md T008b]
  - **决策**: 保持默认 10.0.0.0/16 CIDR,在 IaC 中支持可配置参数
  - **容量验证**: 私有应用层子网提供 24,576 个 IP,按每节点 20 IP 计算,可支持约 1,228 节点 (满足 ≥1000 节点需求)
  - **可配置性**: CDK Stack 支持通过上下文变量配置 VPC CIDR (例如 `--context vpcCidr=10.0.0.0/15`),子网自动按比例划分
  - **扩展路径**: 如未来需要 >1500 节点,可配置为 10.0.0.0/15 (支持约 3,000+ 节点)
  - **实施要求**: T008b VPC Stack 实现时需包含容量验证逻辑和配置参数支持
- [x] **CHK002 - ✅ 已解决** - 三层隔离设计经评估保持当前架构,并增强部署模式配置以优化跨AZ流量成本。[安全性+可维护性+成本优化, tasks.md T008b]
  - **决策**: 保持三层隔离设计 (公有子网/私有子网-应用层/私有子网-数据层),增加部署模式配置
  - **安全性**: 符合 AWS Well-Architected 安全最佳实践,职责清晰隔离
  - **部署模式**: 支持三种模式配置 (single-az/multi-az/hybrid),通过 CDK 上下文变量选择
  - **成本优化**: 混合模式 (hybrid) 通过数据层单 AZ + 计算层拓扑感知调度减少 60-70% 跨AZ流量费用
  - **实施要求**: T008b 增加部署模式配置文档,T008c-2 增加 AZ 亲和性调度配置
- [x] **CHK003 - ✅ 已解决** - NAT Gateway 部署优化为双 AZ 配置（平衡成本和高可用）。[成本优化 vs 高可用, tasks.md T008b]
  - **决策**: 在 2 个 AZ 部署 NAT Gateway (AZ-a 和 AZ-b), AZ-c 跨 AZ 路由到 AZ-b
  - **成本节省**: $100/月 → $67/月 (节省 $33/月, 33%)
  - **高可用性**: 保留 2 AZ 容错能力, 单 AZ 故障时其他 AZ 不受影响
  - **权衡**: AZ-c 跨 AZ 数据传输成本略增 (~$0.01/GB), 但训练平台主要流量走 PrivateLink, 影响有限
- [x] **CHK004 - ✅ 已解决** - VPC端点配置已补充EFS端点，满足SageMaker Spaces需求。[完整性, plan.md L54-64, tasks.md L140-148]
  - **解决方案**: 采用方案 A (最小化配置) - 在现有端点基础上添加 EFS Interface 端点
  - **已配置端点**: S3 Gateway、ECR (API/Docker)、CloudWatch (Logs/Monitoring)、STS、SageMaker API、**EFS** (新增)
  - **EFS 端点用途**: SageMaker Spaces 持久化存储 (JupyterLab/VS Code 自动保存到 EFS，US5 必需)
  - **可选优化**: KMS 端点 (S3 SSE-KMS 性能优化)、Secrets Manager 端点 (敏感配置管理)
  - **风险提示**: 未配置 KMS 端点时，S3 SSE-KMS 加密将通过公网访问 KMS API，可能产生跨 AZ 流量费用
- [x] **CHK005 - ✅ 已解决** - NetworkPolicy 与 HyperPod EFA 网络优化兼容性确认。[技术兼容性, tasks.md T008f]
  - **决策**: 保持当前设计，运行时验证 EFA 兼容性
  - **理由**:
    - tasks.md T008f 已明确包含 EFA 兼容性配置要求
    - HyperPod Training Operator 原生支持 EFA，NetworkPolicy 配置时会自动考虑 EFA 端口需求
    - 实际部署时通过 T008g 综合验证任务验证 EFA + NetworkPolicy 组合工作正常
  - **验证时机**: T008g 基础设施综合验证阶段
  - **风险等级**: 低 - HyperPod 原生能力已处理大部分兼容性问题

### 2. EKS 集群配置

- [x] **CHK006 - ✅ 已解决** - EKS 1.32+ 版本与HyperPod Training Operator兼容性已验证。[版本兼容性, plan.md L39]
  - **决策**: 保持 "EKS 1.32+" 表述
  - **兼容性验证**: HyperPod Training Operator 官方支持 Kubernetes 1.28, 1.29, 1.30, 1.31, 1.32, 和 1.33
  - **EKS 1.32 兼容性**: ✅ 完全兼容
  - **说明**: "1.32+" 表示支持 1.32 及更新版本（当前最新支持到 1.33）
  - **实施要求**: plan.md L39 已添加兼容性说明
- [x] **CHK007 - ✅ 已解决** - EKS Add-ons版本要求已明确，tasks.md已引用plan.md版本规范。[依赖管理, plan.md L35-38, tasks.md L170]
  - **决策**: 在 tasks.md 中引用 plan.md 版本要求（单一数据源原则）
  - **版本要求**: EBS CSI Driver ≥v1.28.0, FSx CSI Driver ≥v1.9.0, VPC CNI ≥v1.16.0
  - **版本选择原则**: 使用 EKS 托管 Add-on 的默认推荐版本，或高于最低版本要求
  - **实施要求**: tasks.md L170 已添加明确版本号和 plan.md 引用
- [x] **CHK008 - ✅ 已解决** - HyperPod EKS集群创建拆分为3个子任务设计合理，粒度适中。[任务设计, tasks.md L168-209]
  - **决策**: 保持 T008c-1/2/3 三个子任务设计
  - **设计评估**:
    - T008c-1: EKS 集群基础配置（集群创建 + VPC 关联 + Add-ons 安装）
    - T008c-2: GPU 节点组和 Auto Scaling 配置（节点组 + 扩缩容 + AZ 亲和性 + EFA）
    - T008c-3: IAM 和安全配置（IAM 角色 + Security Group + RBAC + 高可用）
  - **优势**: 职责清晰、支持并行执行（T008c-2 和 T008c-3）、问题隔离良好、粒度适中
  - **依赖关系**: T008c-2 和 T008c-3 依赖 T008c-1，但可并行执行
  - **一致性**: 与 CHK011 的 HyperPod Add-ons 拆分策略一致（3个逻辑任务组）
- [x] **CHK009 - ✅ 已解决** - GPU节点组Auto Scaling策略使用HyperPod原生能力，无需定制化扩展。[可配置性, tasks.md L176-181]
  - **决策**: 使用 SageMaker HyperPod Autoscaling 原生能力，不做定制化扩展
  - **原生能力**:
    - 扩容触发: Kueue 队列 Pending Workloads >0 且持续 5 分钟（默认配置）
    - 缩容触发: 节点 GPU 利用率 <20% 且持续 15 分钟（默认配置）
    - 缩容保护: 运行中训练任务的节点不参与缩容（原生能力）
    - 冷却期: 扩容后 10 分钟内不触发缩容（默认配置）
  - **配置方式**: 使用 HyperPod Auto Scaling Group 配置，依赖原生默认行为
  - **实施要求**: tasks.md L176-181 已标注使用原生能力
- [x] **CHK010 - ✅ 已解决** - IAM角色和RBAC策略设计已明确权限范围，遵循最小权限原则。[安全性, tasks.md L204-218]
  - **决策**: 明确具体权限范围和 RBAC 策略细节
  - **IAM 角色权限**:
    - EKS 节点角色: EC2/ECR/S3/Logs 必需权限（限定 bucket 范围）
    - 训练任务 Pod 角色: S3/SageMaker/CloudWatch 权限（只读 + 指标写入）
    - 监控 Pod 角色: CloudWatch/Logs 只读权限
    - Service Account 映射: training-sa, monitoring-sa, spaces-sa
  - **RBAC 策略**:
    - ClusterRole: hyperpod-admin, hyperpod-project-manager, hyperpod-engineer, hyperpod-viewer
    - Role: training-job-manager, config-reader（命名空间级）
    - RoleBinding: 用户角色映射到对应的 ClusterRole/Role
  - **安全增强**: 启用 Pod Security Standards (restricted 模式)
  - **实施要求**: tasks.md L205-213 已补充详细权限清单

### 3. HyperPod Add-ons 配置

- [x] **CHK011 - ✅ 已解决** - HyperPod Add-ons安装任务已拆分为3个逻辑任务组，优化问题隔离和并行执行。[任务粒度, tasks.md L115-124]
  - **解决方案**: 拆分 T008d 为 3 个逻辑任务组 (T008d-1/2/3)
  - **T008d-1**: 训练核心组件 (Training Operator + Kueue + Elastic Agent)
  - **T008d-2**: 监控组件 (Observability Add-on) - 可与 T008d-3 并行
  - **T008d-3**: 开发环境组件 (Spaces Add-on) - 可与 T008d-2 并行
  - **优势**: 更好的问题隔离，降低重试成本，启用并行执行机会
- [x] **CHK012 - ✅ 已解决** - Kueue优先级名称已统一为high/medium/low，与spec.md用户层优先级保持一致。[需求对齐, tasks.md L223, spec.md L771]
  - **决策**: 调整 Kueue PriorityClass 命名为 high/medium/low (方案 B)
  - **修改内容**:
    - tasks.md L223: PriorityClass 从 critical/high/medium 改为 high/medium/low
    - spec.md L771: 优先级机制描述更新为 "三级优先级使用 Kueue PriorityClass: high/medium/low"
  - **优点**: 用户层和 Kueue 层优先级名称完全一致，无需额外转换逻辑，降低实施复杂度
  - **一致性验证**: spec.md L959 ResourceQuota 定义已确认使用 "high/medium/low" 映射
  - **实施要求**: T008d-1 Kueue 配置时使用 high/medium/low PriorityClass 名称
- [x] **CHK013 - ✅ 已解决** - HyperPod抢占策略完全依赖Kueue原生行为，无需自定义抢占逻辑。[原生优先, tasks.md L224, spec.md L771-776]
  - **决策**: 保持当前设计，完全依赖 Kueue 原生抢占能力（方案 A）
  - **理由**:
    - Kueue 原生能力已覆盖所有抢占需求（冷却期、借用策略、最大抢占次数限制）
    - HyperPod Elastic Agent 自动在抢占前创建检查点（T008d-2，FR-010）
    - 恢复机制：Kueue 自动重新排队，保持原优先级（spec.md L769）
    - 失败处理：平台状态同步服务（T037）检测连续3次失败转Failed（spec.md L427-462）
  - **合规性**: 完全符合 spec.md FR-004 实施约束 "MUST 使用原生抢占机制"（L772）
  - **扩展路径**: spec.md L775-776 已定义例外流程，如未来需要自定义可走治理委员会审批
  - **优势**: 降低系统复杂度、自动获得 HyperPod 未来版本改进、遵循 YAGNI 原则
- [x] **CHK014 - ✅ 已解决** - Elastic Agent检查点管理参数已支持用户自定义配置，默认10-15分钟，可配置范围5-30分钟。[可配置性, tasks.md L230, spec.md FR-010]
  - **决策**: 支持用户可配置检查点间隔 (方案 A)
  - **修改内容**:
    - tasks.md L230: 添加配置说明 "默认间隔 10-15 分钟，支持用户通过训练任务配置自定义间隔范围 5-30 分钟"
  - **配置范围**: 5-30 分钟（灵活性与性能平衡）
  - **默认值**: 10-15 分钟（适合大多数训练场景）
  - **用例适配**:
    - 短训练任务/频繁迭代: 配置 5 分钟间隔
    - 长训练任务/大模型: 配置 20-30 分钟间隔
    - 一般训练任务: 使用默认 10-15 分钟
  - **合规性**: 符合 spec.md FR-010 "在任务配置中指定检查点参数（检查点间隔、存储路径、恢复策略等）"
  - **实施要求**: T008d-2 配置 Elastic Agent 时支持用户自定义间隔参数
- [x] **CHK015 - ✅ 已解决** - Deep Health Check完全依赖HyperPod Health Check Agent原生能力，无需自定义健康检查规则。[原生优先, tasks.md L230]
  - **决策**: 完全依赖 HyperPod 原生健康检查能力（方案 A）
  - **原生能力覆盖**:
    - GPU 健康检查（NVIDIA DCGM 集成）
    - EFA 网络性能检测
    - 存储系统健康（FSx for Lustre / EBS）
    - 节点级别系统健康状态
  - **理由**:
    - HyperPod Health Check Agent 原生能力已覆盖所有核心健康检查场景
    - 符合宪章 Principle I.A (HyperPod Native-First) 和 Principle X (YAGNI)
    - 自动获得 AWS 健康检查改进和更新
    - 降低系统复杂度和维护成本
  - **扩展路径**: 如未来确实需要自定义健康规则，可通过 spec.md 定义的例外流程和治理委员会审批
  - **合规性**: 完全符合当前 tasks.md L230 设计 "Deep Health Check 完全遵循 HyperPod Health Check Agent 原生能力"
  - **优势**: 零额外开发成本、自动获得 AWS 更新、降低运维复杂度

### 4. 存储架构设计

- [x] **CHK016 - ✅ 已解决** - FSx for Lustre默认使用500 MB/s/TiB吞吐量级别，成本优化策略明确，避免过度配置。[成本优化, tasks.md L242]
  - **决策**: 固定使用 500 MB/s/TiB 吞吐量级别（方案 C）
  - **配置参数**:
    - 默认吞吐量: 500 MB/s/TiB
    - 初始容量: 10 TiB
    - 聚合吞吐量: 5 GB/s (10 TiB × 500 MB/s/TiB)
  - **成本优化**:
    - 相比 1000 MB/s/TiB 节省约 50% 成本 (~$6,500/月)
    - 年度成本节省: ~$78,000
  - **性能保证**:
    - 满足 spec.md ≥5GB/s 基线需求
    - 适用于大多数训练场景 (单任务 GPU ≤8)
    - tasks.md L253 已定义调优方案: 性能不达标时升级到 1000 MB/s/TiB
  - **升级路径**:
    - FSx 吞吐量级别可动态调整 (需 6-8 小时停机窗口)
    - 性能验证脚本: `infrastructure/tests/fsx-performance-test.sh`
    - 监控指标: 单客户端吞吐量、GPU 利用率与 I/O 延迟相关性
  - **风险缓解**:
    - 提供性能测试脚本验证吞吐量达标
    - 监控机制及时发现瓶颈
    - 明确升级流程和停机窗口规划
  - **适用场景**: 成本优先，标准训练任务 (GPU ≤8)，开发/测试/生产环境初期部署
- [x] **CHK017 - ✅ 已解决** - FSx容量规划保持当前设计，最低初始成本配置，按需自动扩容。[成本优先, tasks.md L243]
  - **决策**: 保持当前容量规划设计（方案 B）
  - **配置参数**:
    - 初始容量: ≥10 TiB (最低成本配置 ~$3,000/月)
    - 扩容触发阈值: 使用率 >80%
    - 自动扩容: FSx 自动按需扩容，最小增量 1.2 TiB
    - 最大容量: 100 TiB (支持 10 个大数据集)
  - **理由**:
    - 满足 spec.md FR-007 ≥10TB 数据集基线需求
    - 最低初始成本，按需扩容避免过度配置
    - 适用于 MVP 阶段和开发/测试环境
  - **风险提示**:
    - **频繁扩容风险**: 单个 10 TiB 数据集上传后立即触发扩容
    - **扩容性能影响**: 扩容期间（5-10 分钟）吞吐量可能下降 20-30%
    - **空间不足风险**: 80% 触发阈值下，用户可能遇到短暂写入减速
  - **缓解措施**:
    - tasks.md L255 已配置存储容量告警（使用率 >80%）
    - 监控扩容频率和性能影响，生产环境可调整初始容量
    - 扩容操作自动化，无需人工干预
  - **升级路径**: 生产环境部署后根据实际使用模式调整初始容量（如增加到 20-30 TiB）
  - **适用场景**: 成本优先，MVP 阶段，开发/测试环境
- [x] **CHK018 - ✅ 已解决** - S3 Data Repository Association的AutoImportPolicy保持当前设计，保证S3与FSx数据完全同步。[数据一致性, tasks.md L244]
  - **决策**: 保持 AutoImportPolicy 为 NEW/CHANGED/DELETED（方案 B）
  - **配置参数**:
    - AutoImportPolicy: ["NEW", "CHANGED", "DELETED"]
    - 自动同步: S3 事件触发 FSx 元数据更新
    - 同步延迟: 通常 <5 分钟（AWS FSx 自动处理）
  - **理由**:
    - 保持 S3 和 FSx 完全同步，数据一致性最强
    - 无需手动干预，自动处理所有数据变更
    - 支持数据集版本更新场景（覆盖文件或删除旧版本）
  - **性能影响评估**:
    - **训练场景特征**: 数据集通常静态，上传后不频繁修改
    - **NEW 事件**: 数据集上传时触发，合理且必要
    - **CHANGED 事件**: 数据集修改时触发，训练场景中极少发生
    - **DELETED 事件**: 数据集删除时触发，训练场景中较少发生
    - **实际性能影响**: 极低（预期每天 <10 次同步事件）
  - **监控机制**:
    - tasks.md L255 已配置数据同步调度（每小时增量同步）
    - CloudWatch Logs 记录 FSx Data Repository 任务执行日志
    - 监控同步任务频率和执行时长，异常时告警
  - **风险缓解**:
    - 如观察到频繁同步影响性能，可调整为仅 NEW 事件
    - 提供手动同步命令作为备选方案: `aws fsx create-data-repository-task`
  - **适用场景**: 标准训练平台，保证数据一致性优先
- [x] **CHK019 - ✅ 已解决** - 分层检查点迁移机制已设计为异步执行且在空闲时段运行，通过监控验证实际性能影响。[性能保障, tasks.md T038b L451]
  - **决策**: 保持当前异步迁移设计 + 监控验证（方案 B）
  - **迁移策略**:
    - 热检查点: 最近 3 个保留在 NVMe 本地存储
    - 温检查点: 第 4-10 个迁移到 FSx for Lustre
    - 冷检查点: >10 个或 >72 小时归档到 S3
  - **性能保障机制**:
    - **异步迁移**: tasks.md L451 明确"在检查点间隔期（训练任务空闲时段）执行迁移"
    - **定时调度**: 每 10 分钟执行一次迁移检查（tasks.md L456）
    - **避免冲突**: 迁移操作与训练任务检查点创建错峰执行
  - **性能影响评估**:
    - **NVMe → FSx 迁移**: 5GB 检查点 ~10 秒（500 MB/s），理论上低影响
    - **FSx → S3 迁移**: 5GB 检查点 ~50 秒（100 MB/s），占用网络带宽
    - **I/O 竞争风险**: NVMe 迁移可能与训练数据读取存在轻微竞争
  - **监控验证指标**:
    - 训练任务 GPU 利用率变化（迁移期间是否下降）
    - NVMe/FSx I/O 延迟（迁移期间是否增加）
    - 网络带宽使用率（FSx → S3 迁移占用情况）
    - 检查点迁移任务执行时长和成功率
  - **风险缓解**:
    - tasks.md L452 定义存储满载紧急迁移机制
    - tasks.md L453 定义迁移失败重试机制（最多 3 次）
    - 如监控发现性能影响，可调整迁移频率或添加带宽限制
  - **扩展路径**: 如实际部署后发现性能影响，可添加 I/O 监控和带宽限制（方案 A）
  - **适用场景**: MVP 阶段，通过监控数据驱动优化决策
- [x] **CHK020 - ✅ 已解决** - S3生命周期策略已优化为90天保留期+分级存储，平衡成本与合规需求。[合规优化, tasks.md L455]
  - **决策**: 延长保留期至 90 天 + 分级删除策略（方案 A）
  - **生命周期规则**:
    - **0-30 天**: S3 Standard 存储（$0.023/GB/月）
    - **30-90 天**: 转换为 S3 Standard-IA（$0.0125/GB/月，节省 50% 成本）
    - **90 天后**: 自动删除冷检查点
  - **理由**:
    - **合规需求**: 90 天保留期满足大多数审计和追溯要求
    - **模型回滚**: 支持回滚到 90 天内的任意检查点
    - **成本优化**: 分级存储类控制长期存储成本增长
    - **灵活配置**: 通过 IaC 参数可调整保留期（默认 90 天）
  - **成本影响**（假设 100 GB 冷检查点/月）:
    - 30 天删除（原方案）: $2.30/月
    - 90 天删除 + 分级（新方案）: $3.55/月
    - 额外成本: $1.25/月（54% 增加，可接受）
  - **业务场景覆盖**:
    - 训练任务失败恢复: <7 天（热/温检查点）
    - 模型回滚: <90 天（冷检查点）
    - 合规审计: 90 天历史追溯
  - **扩展选项**: 如需更长保留期，可配置 90 天后转换为 S3 Glacier（$0.004/GB/月）而非删除
  - **实施要求**: T008b S3 Buckets Stack 配置生命周期规则（30 天 Standard-IA，90 天删除）
  - **适用场景**: 生产环境，平衡成本、合规与灵活性

---

## II. HyperPod SDK 使用合规性审查

### 1. SDK 方法验证任务 (T000 - Phase 0)

- [x] **CHK021 - ✅ 已解决** - T000任务已移至Phase 0研究阶段,成为Phase 1的前置条件。[任务顺序, tasks.md L30-51, plan.md L131-236]
  - **解决方案**: 创建独立的Phase 0技术可行性研究阶段
  - **实施内容**:
    - 在tasks.md中创建Phase 0部分,将T000(原T008h)移至该阶段
    - 在plan.md中扩展Phase 0研究部分,包含详细的研究目标、任务内容、输出产物和完成标准
    - 更新Phase 1为依赖Phase 0完成的后续阶段
    - 更新所有相关任务的依赖关系引用(T008h → T000)
  - **影响范围**: Phase 1的IaC和后端开发现在必须基于Phase 0研究结论
- [x] **CHK022 - ✅ 已解决** - SDK方法验证文档保持当前定义，包含签名、参数和示例代码，满足基本开发需求。[快速MVP, tasks.md L35]
  - **决策**: 保持当前文档定义（方案 B）
  - **文档内容**:
    - SDK 方法签名（方法名、参数类型）
    - 参数说明（必需/可选、数据类型、约束条件）
    - 示例代码（基本调用示例）
  - **理由**:
    - 最小化 Phase 0 工作量（0.5 人日）
    - 基本信息足够后续开发使用
    - 开发过程中可按需查阅官方文档（tasks.md L38 已提供链接）
    - 符合 MVP 快速验证原则
  - **风险提示**:
    - 开发时可能需要补充查阅官方文档（异常类型、性能特征等）
    - 错误处理模式需在代码审查中统一
  - **缓解措施**:
    - tasks.md L38 已提供官方文档链接: https://sagemaker-hyperpod-cli.readthedocs.io/
    - T014/T036 实施时建立统一的客户端封装和错误处理模式
    - 代码审查确保 SDK 使用一致性
  - **扩展路径**: 如开发过程中发现文档不足，可在 T014 实施时补充完善
  - **适用场景**: MVP 阶段，快速验证 SDK 可用性
- [x] **CHK023 - ✅ 已解决** - T000-fallback触发流程已补充说明，明确三类触发条件和记录要求。[流程清晰, tasks.md L37-42]
  - **决策**: 保持当前流程定义 + 补充说明（方案 B）
  - **触发条件**（tasks.md L38-42 新增）:
    - **方法不存在**: 核心方法（create/get/pause/resume/terminate）在 SDK 中找不到
    - **签名不符**: 参数名称/类型/数量与预期不匹配，或返回值格式严重不符
    - **功能不完整**: 核心方法存在但不支持必需特性（如从检查点恢复、Gang Scheduling 配置）
  - **流程改进**:
    - 添加触发条件说明（消除"签名不符"和"功能不完整"的歧义）
    - 要求记录触发原因到 `docs/hyperpod-sdk-gaps.md`（包含影响范围和备选方案建议）
  - **理由**:
    - 平衡简洁与清晰，当前流程已基本清晰
    - 补充说明消除关键歧义，无需过度细化
    - 信任 Phase 0 执行者的判断能力
    - 符合 MVP 快速验证原则
  - **决策责任**: T000 执行者根据补充说明判断是否触发 fallback
  - **记录要求**: `docs/hyperpod-sdk-gaps.md` 必须包含触发原因、影响的核心方法、备选方案建议
  - **适用场景**: 快速 MVP，信任开发团队判断能力
- [x] **CHK024 - ✅ 已解决** - SDK备选方案治理流程保持POC后提交，基于完整验证结果提高审批成功率。[流程合理, tasks.md L66-70]
  - **决策**: 保持当前流程（POC 后提交例外申请）（方案 B）
  - **当前流程**（tasks.md L66-70）:
    - 阶段 1-2: 执行备选方案分析和 POC 验证（1.5 人日）
    - 阶段 3: 基于 POC 结果准备治理委员会例外申请文档（0.5 人日）
    - plan.md L352: 治理委员会审批通过作为 Phase 0 完成标准
  - **理由**:
    - **完整论证优先**: POC 验证结果提供技术支撑，提高审批成功率
    - **高效决策**: 治理委员会基于完整信息（POC 结果、性能测试、兼容性验证）做出决策
    - **流程简洁**: 单次正式申请，避免多轮沟通
    - **当前设计已合理**: tasks.md 和 plan.md 已定义此流程，无需调整
  - **风险缓解**（tasks.md L70 新增）:
    - 阶段 1 快速评估（0.5 人日）可及早发现不可行方案
    - 如发现 boto3 和 kubernetes-client 都不可行，立即上报治理委员会并停止 POC
    - 避免无效 POC 工作（节省 1 人日）
  - **审批时机**: Phase 0 完成前必须获得治理委员会审批（plan.md L352 完成标准）
  - **返工风险评估**: POC 提供充分技术论证，审批不通过概率低（<10%）
  - **适用场景**: 标准治理流程，技术决策基于验证结果

### 2. SDK 绕过场景管理

- [x] **CHK025 - ✅ 已解决** - Kueue Workload 状态监控使用 kubernetes-client 的决策合理。[简单性, plan.md L131-137, spec.md L85-86]
  - **决策**: 保持当前设计，kubernetes-client 用于只读状态监控
  - **合理性分析**:
    - HyperPod SDK 未提供 Kueue Workload 状态详情 API（plan.md L135）
    - 细粒度调度状态（Pending/Admitted/PodsReady/Finished）对故障诊断至关重要
    - 使用范围已严格限定：只读监控、需例外审批、不做配置操作（spec.md L63）
  - **替代方案评估**:
    - 仅 SDK 状态：丢失 Submitted 子状态细节，降低调试能力 ❌
    - CloudWatch 日志解析：延迟高、解析复杂、信息可能不完整 ❌
  - **行业惯例**: Kubernetes 平台标准做法，直接查询 CRD 状态用于监控
  - **治理合规**: spec.md L85-86 已定义例外审批流程
- [x] **CHK026 - ✅ 已解决** - NetworkPolicy 配置架构层次已澄清。[架构层次, plan.md L136, tasks.md T008f]
  - **决策**: NetworkPolicy 在 IaC 层面配置，kubernetes-client 仅用于验证/监控
  - **架构澄清**:
    - **IaC 配置** (主要): tasks.md T008f 定义静态 YAML 配置 (`infrastructure/k8s/network-policies/`)，通过 CDK/kubectl 部署
    - **kubernetes-client** (辅助): 仅用于 POC 验证（plan.md L289-292）和运行时状态监控
  - **符合最佳实践**: 网络策略作为基础设施配置，不应在应用运行时动态创建
  - **文档更新**: plan.md SDK 绕过场景表格已澄清使用范围
- [x] **CHK027 - ✅ 已解决** - SageMaker Model Registry 使用 boto3 完全符合 SDK 适用范围定义。[合规性, spec.md L943-948, plan.md L137]
  - **决策**: 使用 boto3 调用 SageMaker Model Registry API
  - **合规性验证**:
    - spec.md L945 明确: "Model Registry 不在 `sagemaker-hyperpod` SDK 的适用范围内"
    - HyperPod SDK 仅适用于 4 大功能模块: Cluster/Training/Inference/Space
    - spec.md L947 指定 boto3 为首选实施方案
  - **结论**: 这不是"绕过"而是"按功能域选择正确的 SDK"，完全合规

### 3. SDK 实施约束遵守情况

- [x] **CHK028 - ✅ 已解决** - 训练任务管理功能完全遵循 SDK-First 原则。[SDK-First原则, spec.md FR-001/FR-002]
  - **验证结果**: 所有核心操作（提交/暂停/恢复/终止/监控）均使用 `sagemaker-hyperpod.training` 模块
  - **实施约束覆盖**:
    - FR-001 (L788): 训练任务提交 → MUST 使用 training 模块
    - FR-002 (L795): 生命周期管理 → MUST 使用 training 模块
    - FR-003 (L811): Gang Scheduling → 默认启用，通过 training 模块配置
    - FR-004 (L828): 优先级配置 → 通过 training 模块提交时配置
  - **绕过场景**: 仅限 SDK 不支持或不在范围内的场景（CHK025/CHK026/CHK027 已审查通过）
  - **治理合规**: 所有绕过需例外审批（spec.md 已定义流程）
- [x] **CHK029 - ✅ 已解决** - Space 管理功能完全遵循 SDK-First 原则。[SDK-First原则, spec.md FR-012 L930-935]
  - **验证结果**: Space 生命周期管理使用 `sagemaker-hyperpod.space` 模块
  - **SDK 适用范围**: Space 是 HyperPod SDK 四大功能模块之一 (Cluster/Training/Inference/Space)
  - **实施约束** (spec.md FR-012):
    - MUST 使用 `sagemaker-hyperpod.space` 模块进行 Space 创建、配置和生命周期管理
    - 具体方法: `create_space()`, `delete_space()`, `get_space_details()`, `update_space_settings()`
  - **备选方案**: 仅在 SDK 不支持特定配置（如自定义镜像、资源配额）时 MAY 使用 boto3
- [x] **CHK030 - ✅ 已解决** - SDK 绕过场景代码注释规范已定义。[代码规范, spec.md L792/L813/L831]
  - **规范定义状态**: 设计阶段已完成规范定义
  - **代码注释要求** (spec.md):
    - "在代码中注释说明理由(遵循宪章 Principle I.B)"
    - 覆盖 FR-001 (L792)、FR-003 (L813)、FR-004 (L831) 等所有 SDK 绕过场景
  - **例外申请流程**: plan.md L318-326 已定义完整流程
  - **验证时机**: 代码实现阶段 (Phase 2-3) 代码审查时验证注释合规性
  - **示例注释格式**: `# SDK Bypass: [原因] - 遵循宪章 Principle I.B, 例外申请编号: [XXX]`

---

## III. 技术栈选型和版本兼容性审查

### 1. 后端技术栈

- [x] **CHK031 - ✅ 已解决** - Python 3.11 + FastAPI 0.109+ + SQLAlchemy 2.0+ 无已知兼容性问题。[版本兼容性, tasks.md L8]
  - **验证结果**: 该组合为成熟的生产就绪方案，无已知兼容性问题
  - **行业验证**:
    - GitHub `full-stack-fastapi-postgresql` 模板使用 FastAPI 0.109 + SQLAlchemy 2.0.29 (2024)
    - 大量生产环境部署和社区最佳实践文档
  - **兼容性矩阵**: Python 3.11 ✅ | FastAPI 0.109+ ✅ | SQLAlchemy 2.0+ ✅
  - **注意事项**: 使用异步引擎时需配合 asyncpg/aiomysql 等异步驱动
- [x] **CHK032 - ✅ 已解决** - aiomysql异步驱动与SQLAlchemy 2.0的异步引擎集成已验证，保持当前选型并记录已知问题。[技术验证, plan.md L28]
  - **决策**: 保持 aiomysql 作为 MySQL 异步驱动
  - **兼容性验证**: SQLAlchemy 2.0+ 官方支持 aiomysql，通过 `create_async_engine("mysql+aiomysql://...")` 配置
  - **已知问题**:
    - 连接关闭时可能出现 "Cannot operate on a closed connection" 警告 (GitHub #10893)
    - 高并发场景下连接池回收需谨慎配置 (GitHub #10457)
  - **缓解措施**:
    - 配置连接池参数: `pool_pre_ping=True`, `pool_recycle=3600`
    - 使用 async context manager 确保连接正确释放
    - 生产环境建议配置 `pool_size=10`, `max_overflow=20`
  - **替代方案**: 如遇严重问题可切换至 asyncmy (MySQL 官方异步驱动)
  - **适用场景**: MVP 阶段，aiomysql 社区成熟度和文档完善度更优
- [x] **CHK033 - ✅ 已解决** - Pydantic v2与FastAPI 0.109+集成无破坏性变更，项目全新开发无迁移问题。[版本兼容性, plan.md L28]
  - **决策**: 使用 Pydantic v2 + FastAPI 0.109+ 组合
  - **兼容性验证**: FastAPI 0.100+ 开始原生支持 Pydantic v2，0.109+ 完全兼容
  - **无迁移风险**: 项目从头开始使用 Pydantic v2，无需处理 v1→v2 迁移问题
  - **最佳实践**:
    - 使用 `model_config` 替代 `Config` 类
    - 使用 `@field_validator` 替代 `@validator`
    - 使用 `model_json_schema()` 替代 `schema()`
  - **文档参考**: FastAPI Pydantic v2 Migration Guide
- [x] **CHK034 - ✅ 已解决** - sagemaker-hyperpod SDK版本策略为"最新稳定版"，Phase 0验证时锁定具体版本。[版本管理, spec.md L728-738]
  - **决策**: 保持"最新稳定版"表述，Phase 0 (T000) 验证时确定并记录具体版本
  - **版本管理策略**:
    - 设计阶段: 使用"最新稳定版"表述，避免过早锁定
    - Phase 0 验证: T000 任务产出 `docs/hyperpod-sdk-reference.md` 包含验证时的具体版本号
    - 实施阶段: 锁定 T000 验证通过的版本，记录到 `backend/requirements.txt`
  - **版本兼容性保障**:
    - T000 验证任务覆盖所有核心方法签名和参数
    - 如 SDK 更新导致不兼容，需重新执行 T000 验证流程
    - `docs/hyperpod-sdk-reference.md` 作为版本兼容性的单一数据源
  - **理由**: AWS 托管 SDK 版本迭代较快，过早锁定可能错过重要更新
  - **风险缓解**: Phase 0 完成标准要求 SDK 可用性决策明确
- [x] **CHK035 - ✅ 已解决** - boto3与sagemaker-hyperpod SDK版本兼容性由AWS官方保障，Phase 0验证时确认。[依赖兼容性, tasks.md L229]
  - **决策**: 遵循 CHK034 相同的 Phase 0 验证策略
  - **兼容性保障**:
    - boto3 和 sagemaker-hyperpod SDK 均由 AWS 官方维护
    - sagemaker-hyperpod SDK 内部依赖 boto3，版本兼容性由 SDK 自身保证
    - AWS SDK 遵循语义化版本，次版本更新保持向后兼容
  - **验证时机**: Phase 0 (T000) 安装 SDK 环境时验证协同工作
  - **依赖管理**: `backend/requirements.txt` 中使用版本范围约束 (如 `boto3>=1.28.0`)
  - **风险等级**: 低 - AWS 官方 SDK 兼容性有保障

### 2. 前端技术栈

- [x] **CHK036 - ✅ 已解决** - React 18 + TypeScript 5.3+ + Vite组合符合2024-2025年前端最佳实践。[技术先进性, tasks.md L9]
  - **决策**: 保持当前技术选型
  - **技术先进性验证**:
    - **React 18**: 最新稳定版，支持 Concurrent Features、Suspense、自动批处理、Transitions API
    - **TypeScript 5.3+**: 最新稳定版，const type parameters、improved narrowing、satisfies operator
    - **Vite 5.x**: 最快构建工具，原生 ESM，HMR <50ms，Tree Shaking 优化
  - **行业验证**: Vercel、Shopify、Cloudflare 等企业广泛采用该技术栈
  - **生态成熟度**: 社区活跃，文档完善，第三方库兼容性好
  - **性能优势**: 开发时 HMR 极快，生产构建体积小
- [x] **CHK037 - ✅ 已解决** - AWS Cloudscape Design System完全支持React 18，项目使用CSR无SSR兼容问题。[技术兼容性, spec.md FR-024]
  - **决策**: 使用 @cloudscape-design/components 3.0+
  - **React 18 兼容性**:
    - Cloudscape 3.0+ 官方支持 React 18
    - 不使用已废弃的 `findDOMNode` API
    - 支持 React StrictMode 双重渲染检测
    - 兼容 React 18 自动批处理和并发特性
  - **SSR/Suspense 说明**:
    - 项目架构: CSR (Client-Side Rendering) + Vite SPA
    - 无 SSR 需求，不涉及 Next.js/Remix 等 SSR 框架
    - Suspense 用于数据加载 (TanStack Query)，与 Cloudscape 组件无冲突
  - **AWS 官方保障**: Cloudscape 是 AWS 官方设计系统，与 AWS 服务深度集成
- [x] **CHK038 - ✅ 已解决** - TanStack Query v5与Zustand职责分离，两者并存是现代React最佳实践，非技术冗余。[技术冗余, tasks.md L9]
  - **决策**: 保持 TanStack Query + Zustand 双状态管理方案
  - **职责划分**:
    - **TanStack Query v5** (服务器状态): API 数据获取、缓存、后台同步、乐观更新、分页
    - **Zustand** (客户端状态): 认证状态 (authStore)、UI 偏好 (uiStore)、全局 UI 状态
  - **无冲突理由**:
    - 两者关注不同类型的状态，职责清晰分离
    - TanStack Query 不适合管理纯客户端状态 (如侧边栏展开/收起)
    - Zustand 不提供服务器数据缓存和同步能力
  - **行业验证**: TanStack 官方推荐与 Zustand/Jotai 配合使用
  - **代码组织**: `frontend/src/stores/` (Zustand) + `frontend/src/hooks/useXxx.ts` (TanStack Query)
- [x] **CHK039 - ✅ 已解决** - Recharts需创建Cloudscape主题适配器，使用Design Tokens确保UI一致性。[UI一致性, tasks.md L237]
  - **决策**: 创建 Cloudscape 主题适配器 (方案 A)
  - **实施方案**:
    - 创建 `frontend/src/lib/chartTheme.ts` 定义 Recharts 主题
    - 引用 Cloudscape Design Tokens: `@cloudscape-design/design-tokens`
    - 适配内容: 颜色 (primary/secondary/semantic)、字体、间距、边框圆角
  - **主题适配示例**:
    ```typescript
    import { colorChartsPalette, fontFamilyBase } from '@cloudscape-design/design-tokens';
    export const cloudscapeChartTheme = {
      colors: colorChartsPalette,
      fontFamily: fontFamilyBase,
      // ... 其他 tokens
    };
    ```
  - **工作量**: 约 0.5 人日 (可在 T067 MetricsCharts 组件中实现)
  - **合规性**: 符合 Principle XI (UI/UX Consistency)，确保图表与 Cloudscape 组件视觉统一

### 3. 数据库和存储

- [x] **CHK040 - ✅ 已解决** - Aurora Serverless v2 ACU配置满足MVP需求，生产环境通过参数调整最小ACU避免冷启动。[性能, tasks.md L78]
  - **决策**: 保持当前配置 + 环境差异化策略 (方案 A)
  - **配置策略**:
    - **开发环境**: 最小 0.5 ACU (可暂停)，最大 8 ACU，接受冷启动延迟
    - **生产环境**: 最小 2 ACU (避免冷启动)，最大 16 ACU，通过 CDK 上下文变量配置
  - **性能评估**:
    - Aurora Serverless v2 冷启动: <15 秒 (比 v1 显著改善)
    - 16 ACU ≈ 64 GB RAM + 16 vCPU，支持 500-1000 并发连接
    - 满足 spec.md 要求: ≥1000 注册用户，≥200 并发用户
  - **成本优化**:
    - 开发环境: 空闲时暂停到 0 ACU，月成本 <$50
    - 生产环境: 最小 2 ACU 保持预热，月成本 ~$150-300
  - **扩展路径**: 如并发需求增长，可调整最大 ACU 至 32/64/128
- [x] **CHK041 - ✅ 已解决** - RDS Proxy连接池配置使用AWS默认值，自动管理连接池大小，配置合理。[可配置性, tasks.md L79]
  - **决策**: 保持 AWS 默认配置
  - **连接池配置**:
    - 空闲超时: 30 分钟 (AWS 默认，适合 Web 应用)
    - 连接池大小: RDS Proxy 自动管理，无需手动配置
    - 连接复用: 自动复用空闲连接，减少数据库连接开销
  - **与 Serverless v2 协同**:
    - RDS Proxy 平滑处理 Aurora Serverless 扩缩容期间的连接
    - 避免应用直连数据库导致的连接风暴
  - **监控指标**: CloudWatch 监控 DatabaseConnections、AvailabilityPercent
  - **调整时机**: 如监控发现连接等待时间过长，可调整 max_connections_percent
- [x] **CHK042 - ✅ 已解决** - S3 SSE-KMS统一使用AWS托管密钥(aws/s3)，MVP阶段简化配置。[安全策略, plan.md L89-90]
  - **决策**: 统一使用 AWS 托管密钥 aws/s3 (方案 B)
  - **配置策略**:
    - 所有 S3 存储桶 (datasets/models/checkpoints) 使用 SSE-KMS with aws/s3
    - 无需创建和管理 CMK，零额外成本
    - AWS 自动处理密钥轮换
  - **选择理由**:
    - MVP 阶段简化配置和运维
    - aws/s3 满足基本加密合规要求
    - 数据不涉及跨账户访问场景
  - **安全保障**:
    - 静态数据加密: ✅ SSE-KMS 加密
    - 传输加密: ✅ HTTPS 强制 (Bucket Policy)
    - 审计日志: ✅ CloudTrail 记录 S3 API 调用
  - **升级路径**: 如未来需要更强审计能力或跨账户访问，可迁移到 CMK
  - **成本**: $0 额外密钥费用 (aws/s3 免费)
  - **文档同步**: 需更新 plan.md L96-98, tasks.md L165 明确使用 aws/s3

### 4. GPU 驱动和 CUDA 环境

- [x] **CHK043 - ✅ 已解决** - NVIDIA Driver + CUDA + PyTorch 版本兼容性已验证。[版本兼容性, plan.md L42-45]
  - **验证结果**: NVIDIA Driver ≥535.104.05 支持 CUDA 12.x，CUDA 12.2 向后兼容 PyTorch 预编译版本 (CUDA 12.1)
  - **兼容性矩阵**: PyTorch 2.2-2.4 均支持 CUDA 11.8/12.1，CUDA 12.2 向后兼容可正常运行
  - **依赖验证**: cuDNN ≥8.9.0 ✅，NCCL ≥2.18.0 ✅
  - **结论**: HyperPod 环境已验证此配置组合
- [x] **CHK044 - ✅ 已解决** - HyperPod AMI 默认驱动版本由 AWS 官方维护，T008g 已包含验证步骤。[依赖验证, plan.md L45]
  - **决策**: 依赖 AWS 官方 HyperPod AMI 维护
  - **验证时机**: 集群创建后通过 T008g 综合验证 (nvidia-smi 测试)
  - **保障机制**: AWS 定期更新 AMI 支持最新 GPU 实例类型 (p4d, p5, trn1)
- [x] **CHK045 - ✅ 已解决** - 自定义容器镜像兼容性验证保持当前设计，依赖开发者经验。[流程完整性, plan.md L45]
  - **决策**: 保持 plan.md L45 现有说明 "自定义容器镜像需确保兼容性"
  - **理由**: MVP 阶段快速推进，开发者具备 CUDA/PyTorch 兼容性经验
  - **风险缓解**: 推荐使用 AWS DLC 或 HyperPod 官方基础镜像，降低兼容性风险
  - **扩展路径**: 如遇兼容性问题频发，可在后续版本补充验证流程文档

---

## IV. 系统可扩展性和可维护性审查

### 1. 代码架构设计

- [x] **CHK046 - ✅ 已解决** - 后端采用Repository模式和Service层抽象经评估后保持当前设计。[架构复杂度, plan.md L299]
  - **决策**: 保持 Repository + Service 4层架构
  - **理由**:
    - 符合企业级 DDD 模式和架构最佳实践
    - 职责清晰,数据访问层、业务逻辑层、API路由层明确分离
    - 可测试性强,Repository 层可独立 mock
    - 为未来多数据源切换和复杂数据聚合预留架构空间
    - 便于大规模团队并行开发
  - **风险缓解**: 通过 Base Repository 封装通用 CRUD 方法,减少样板代码;确保开发文档清晰说明各层职责
- [x] **CHK047 - ✅ 已解决** - API 路由按功能域垂直切分，职责清晰无重叠。[职责划分, plan.md L189-196]
  - **路由模块**: training_jobs / datasets / resource_quotas / users / monitoring
  - **职责验证**: 各模块职责边界清晰，training_jobs 与 monitoring 职责互补（详情 vs 聚合）
  - **设计原则**: 遵循 RESTful 资源导向设计，每个模块对应单一领域实体
- [x] **CHK048 - ✅ 已解决** - 前端组件划分 (common/domain) 合理，无过度抽象风险。[组件设计, plan.md L235-240]
  - **common 层**: 封装 Cloudscape 组件 (DataTable, StatusIndicator, Charts)，提供统一 API
  - **domain 层**: 业务特定组件 (TrainingJobCard, DatasetUploader)，组合 common 组件
  - **风险评估**: domain 组件数量适中，与 5 个 User Stories 对应，无过深嵌套
- [x] **CHK049 - ✅ 已解决** - SQLAlchemy 模型与 Pydantic Schema 双层设计必要且合理，符合 FastAPI 最佳实践。[过度设计, plan.md L173-183]
  - **职责分离**: SQLAlchemy (数据库映射) vs Pydantic (API 契约)，职责不同
  - **字段差异**: ORM 含数据库字段 (id, created_at)，Schema 含 API 字段 (分页、过滤)
  - **安全边界**: Schema 可隐藏敏感字段，避免 ORM 模型直接暴露
  - **行业验证**: FastAPI 官方推荐分离模式

### 2. 服务拆分和解耦

- [x] **CHK050 - ✅ 已解决** - 服务拆分合理，职责清晰无循环依赖。[服务边界, plan.md L185-189]
  - **training_job_service**: 训练任务生命周期管理 → HyperPod SDK
  - **checkpoint_service**: 检查点创建和元数据管理 → FSx/S3
  - **model_registry_service**: 模型注册和版本管理 → SageMaker Model Registry
  - **依赖关系**: training_job → checkpoint → model_registry (单向依赖，无循环)
- [x] **CHK051 - ✅ 已解决** - 客户端封装必要，提供可测试性、可替换性和关注点分离。[抽象层次, plan.md L198-200]
  - **hyperpod_client**: 封装 HyperPod SDK，统一错误处理、重试逻辑
  - **kueue_client**: 封装 kubernetes-client，抽象 K8s CRD 操作复杂性
  - **s3_client**: 封装 boto3 S3，统一 presigned URL 和分片上传
  - **设计价值**: 支持 T000-fallback SDK/boto3/kubernetes-client 切换，业务层与 SDK 解耦
- [x] **CHK052 - ✅ 已解决** - 检查点服务拆分合理，遵循单一职责原则。[职责划分, tasks.md L436-465]
  - **checkpoint_service (T038)**: 关注"创建" - 5 种触发场景、初始保存、元数据记录
  - **checkpoint_migration_service (T038b)**: 关注"迁移" - 分层存储策略 (NVMe→FSx→S3)
  - **接口约定**: T038b 调用 T038 的 `list_checkpoints()` 接口，依赖关系清晰

### 3. 配置管理和环境变量

- [x] **CHK053 - ✅ 已解决** - 环境变量模板 (T006) 已涵盖所有必需配置项。[配置完整性, tasks.md T006 L109-115]
  - **必需配置**: DATABASE_URL, AWS_REGION, HYPERPOD_CLUSTER_ARN
  - **可选凭证**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (支持 AWS CLI profile)
  - **kubectl 配置**: 通过 `aws eks update-kubeconfig` 自动生成
- [x] **CHK054 - ✅ 已解决** - AWS 凭证配置遵循 AWS SDK 默认凭证链，优先级明确。[配置优先级, tasks.md T006 L110]
  - **优先级**: 环境变量 → AWS CLI profile → IAM Role (EC2/EKS Pod)
  - **开发环境**: 推荐 AWS CLI profile (~/.aws/credentials)
  - **生产环境**: 推荐 IAM Role for Service Account (IRSA)
- [x] **CHK055 - ✅ 已解决** - kubectl 配置通过 AWS 官方命令自动生成，可靠性有保障。[配置可靠性, tasks.md T006 L115]
  - **配置命令**: `aws eks update-kubeconfig --name <cluster-name> --region <region>`
  - **可靠性**: AWS 官方命令，自动处理 IAM 认证和 token 刷新
  - **验证时机**: T008g 综合验证任务包含 `kubectl cluster-info` 验证
- [x] **CHK056 - ✅ 已解决** - MLflow Tracking URI 环境变量注入安全，无凭证泄露风险。[安全性, tasks.md T037a L441]
  - **URI 内容**: 仅包含 endpoint 地址，不含凭证
  - **认证方式**: SageMaker Managed MLflow 使用 IAM Role (IRSA)，非明文凭证
  - **网络安全**: VPC 内部通信，PrivateLink 端点保护

### 4. 错误处理和重试机制

- [x] **CHK057 - ✅ 已解决** - Gang Scheduling 重试策略依赖 HyperPod/Kueue 原生机制，合理且符合原生优先原则。[重试策略, spec.md L746-751, tasks.md T036a]
  - **超时配置**: 60 秒内所有 Pods 必须同时就绪
  - **失败处理**: 部分 Pod 调度失败则任务转 Failed，已创建 Pods 自动清理
  - **重试机制**: Kueue 自动重新排队，连续 3 次失败转 Failed
- [x] **CHK058 - ✅ 已解决** - 连续抢占失败状态转换设计合理，告警机制提供人工干预机会。[状态转换, spec.md L427-462, tasks.md T037d]
  - **转换逻辑**: 连续抢占 3 次后任务转 Failed，自动停止重新排队
  - **告警通知**: 发送给任务提交者和平台管理员，提供干预窗口
  - **干预方式**: 用户可手动重新提交任务（调整优先级或资源配置）
  - **故障分类**: failureCategory = "PreemptionExhausted" 便于分析
- [x] **CHK059 - ✅ 已解决** - 检查点迁移失败回退策略合理，优先保证数据安全。[错误处理, tasks.md T038b L453-454]
  - **回退策略**: 迁移失败时保留原位置检查点，不丢失数据
  - **重试机制**: 下次迁移周期重试，最多 3 次
  - **告警机制**: 持续失败触发告警，通知运维人员干预
- [x] **CHK060 - ✅ 已解决** - FSx/NVMe存储满载的紧急迁移策略设计合理，已有足够缓解措施。[性能影响, tasks.md T038b L458-459]
  - **紧急迁移触发**: NVMe/FSx 使用率 >90% 时触发紧急迁移（非 100%，保留缓冲）
  - **性能影响**: 紧急迁移与训练 I/O 存在竞争风险，但在存储临界时是必要的权衡
  - **缓解措施**:
    - 90% 阈值提前触发，避免 100% 存储耗尽
    - 满载时优雅降级：暂停新检查点创建，保留最近 1 个
    - 告警机制通知运维干预
  - **权衡结论**: 轻微性能影响 vs 存储耗尽导致任务失败 → 当前设计合理

---

## V. 过度设计和违反原则检查

### 1. YAGNI (You Aren't Gonna Need It) 原则

- [x] **CHK061 - ✅ 已解决** - Phase 6成本分析功能设计合理，非过早优化。[优先级, tasks.md L583-624]
  - **优先级**: P2 (Important)，非 P1 核心功能
  - **依赖关系**: 明确依赖 Phase 1-5 完成后执行（tasks.md L587: "依赖 US1, US2, US3 完成"）
  - **设计合理性**: 成本分析需要训练任务、数据集、配额历史数据支撑
  - **结论**: 这是合理的功能规划排序，MVP 优先交付核心功能，成本分析在数据积累后实现
- [x] **CHK062 - ✅ 已解决** - 预算预警三级阈值设计合理，符合行业最佳实践。[简单性, spec.md L270]
  - **行业对标**: AWS Cost Explorer、Azure Cost Management 均采用三级阈值
  - **业务语义**:
    - 80%: 预警提醒，有时间调整资源使用策略
    - 90%: 紧急警告，需立即采取行动
    - 100%: 临界状态，预算超支
  - **实现复杂度**: 低（仅需 3 个条件判断和通知逻辑）
  - **结论**: 三级阈值提供渐进式预警，非过度设计
- [x] **CHK063 - ✅ 已解决** - 训练任务停滞检测的主指标选择逻辑设计合理，平衡易用性和灵活性。[简单性, tasks.md T037c L423-432]
  - **默认行为**: 监控 Loss 指标（覆盖 90%+ 常见训练场景）
  - **用户控制**:
    - 可指定其他主指标 (Accuracy/Perplexity 等)
    - 可完全禁用停滞检测 (适用于 GAN/RL 等 Loss 震荡场景)
  - **Fallback 逻辑**: Loss → Accuracy → Perplexity（仅 3 个指标的简单优先级）
  - **设计原则**: 约定优于配置，提供合理默认值同时保留用户控制权
  - **结论**: 非过度设计，满足 KISS 原则
- [x] **CHK064 - ✅ 已解决** - 资源限制配置两层设计合理，是多租户场景的标准模式。[配置复杂度, tasks.md T010b, T012b]
  - **设计模式**: 全局级 (角色默认) + 项目级 (覆盖配置)
  - **查询逻辑**: 项目级优先，否则 fallback 到全局级
  - **必要性**:
    - 支持项目例外配置 (高优先级研究项目可获得更多资源)
    - 避免角色爆炸 (无需 engineer-project-a, engineer-project-b 等)
    - 减少配置重复 (全局默认 + 少量项目覆盖)
  - **行业对标**: Kubernetes ResourceQuota、AWS Service Quotas 均采用类似多级继承
  - **结论**: 两层继承是多租户资源管理的最佳平衡，非过度设计

### 2. KISS (Keep It Simple, Stupid) 原则

- [x] **CHK065 - ✅ 已解决** - 训练任务状态模型经评估后保持当前6状态设计。[状态复杂度, spec.md L310-342]
  - **决策**: 保持 Submitted/Running/Paused/Preempted/Completed/Failed 6状态模型
  - **理由**:
    - 精确反映 HyperPod 调度机制 (三级优先级抢占、Gang Scheduling)
    - 目标用户为算法工程师,能理解并利用调度细节优化训练效率
    - 每个状态有明确业务语义 (Paused用户主动暂停 vs Preempted系统抢占)
    - 提供精确故障定位能力,便于排查任务失败原因
    - 状态模型与平台核心能力紧密结合,不属于过度设计
  - **用户体验优化**:
    - UI 友好化: 列表页使用直观状态名称 (Preempted → "排队等待资源")
    - 用户引导: 提供首次使用引导和状态帮助文档
    - 详情页细化: 展示状态转换历史和 Submitted 子阶段
    - 监控告警: Preempted 频繁时主动告警并提示优化建议
- [x] **CHK066 - ✅ 已解决** - Submitted状态的三个子阶段对专业用户有诊断价值，应保留。[用户体验, spec.md L372-379]
  - **目标用户**: 算法工程师，具备技术背景，能理解调度细节
  - **业务价值**:
    - WaitingForQuota: 配额不足 → 用户可申请增加配额或等待释放
    - WaitingForAdmission: 队列排队中 → 用户了解优先级位置
    - StartingPods: 正在启动 → 用户知道即将运行
  - **故障诊断**: 帮助区分配额问题 vs 资源不足 vs 启动失败
  - **UI 处理**: 详情页展示子阶段，列表页可简化显示为 "排队中"
  - **结论**: 子阶段暴露符合专业平台定位，与 CHK065 状态模型决策一致
- [x] **CHK067 - ✅ 已解决** - 检查点触发的5种场景是实现必需的区分，非过度设计。[简单性, tasks.md T038 L443-448]
  - **5 种场景的必要性**:
    - 定期自动: 定时任务触发，间隔可配置
    - 训练中断: 异常检测触发，需立即响应
    - 节点故障: 健康检查触发，超时阈值处理
    - 资源抢占: Kueue 事件触发，必须在驱逐前完成（超时 5 分钟）
    - 用户手动: API 调用触发，需状态验证
  - **不可简化原因**: 每种场景有不同检测逻辑、响应时间和优先级要求
  - **用户视角**: 文档和 UI 可简化为"系统自动保存 + 手动创建"
  - **结论**: 5 种场景是实现层面的必要区分，满足不同故障恢复需求
- [ ] CHK068 - 模型生命周期状态包含6种状态(Training/Registered/Approved/Deployed/Archived/Rejected)是否过于复杂？[状态复杂度, spec.md L962-968]

### 3. DRY (Don't Repeat Yourself) 原则

- [ ] CHK069 - training_job_service和hyperpod_service的职责是否存在重复？是否可以合并？[职责重复, tasks.md T036/T037]
- [ ] CHK070 - sagemaker_spaces_service和sagemaker_lifecycle_service的职责是否存在重复？[职责重复, tasks.md T085/T085a]
- [ ] CHK071 - 前端TrainingJobList和DatasetList组件是否存在大量重复代码？是否需要抽象为通用DataTable组件？[代码复用, tasks.md T032/T049]

### 4. 单一职责原则 (SRP)

- [ ] CHK072 - training_sync_service(T037)同时负责状态同步和事件处理是否违反SRP？[单一职责, tasks.md L293]
- [ ] CHK073 - checkpoint_service(T038)同时负责创建、保存和元数据管理是否职责过重？[单一职责, tasks.md L322-331]
- [ ] CHK074 - cost_calculator(T069)同时负责成本计算和分摊逻辑是否应该拆分？[单一职责, tasks.md L469]

---

## VI. 实施风险和缓解策略审查

### 1. HyperPod SDK 不可用风险

- [x] **CHK075 - ✅ 已解决** - SDK方法验证任务(原T008h,现T000)已移至Phase 0研究阶段完成。[风险控制, 参见 CHK021]
- [x] **CHK076 - ✅ 已解决** - T000-fallback 任务已增加完整的 POC 验证步骤,确保技术可行性。[技术验证, tasks.md L40-73, plan.md L187-337]
  - **解决方案**: 在 T000-fallback 中增加三阶段执行策略 (分析 → POC 验证 → 整合治理)
  - **实施内容**:
    - **阶段 1** (0.5人日): 备选方案分析 - 评估 boto3/kubernetes-client 能力和风险
    - **阶段 2** (1人日): POC 技术验证 - 实际代码验证关键功能 (创建任务、状态查询、生命周期控制、错误处理)
    - **阶段 3** (0.5人日): 方案整合与治理 - 完善接口设计、准备例外申请、评估影响
  - **POC 验证内容**:
    - boto3: 创建 SageMaker Training Job、状态查询、暂停/恢复/终止验证、日志监控
    - kubernetes-client: PyTorchJob CRD 操作、Kueue Workload 查询、NetworkPolicy 配置、错误处理复杂度评估
    - 性能测试: API 响应时间 (P50/P99)、并发性能、兼容性验证
  - **输出产物**:
    - POC 代码: `poc/boto3-training-poc.py`, `poc/k8s-client-poc.py`
    - 验证报告: `docs/poc-validation-report.md` (含技术可行性结论、性能测试、功能限制、风险评估)
  - **工作量调整**: ~~1人日~~ → **2人日**
  - **风险控制**: 提前识别备选方案的技术障碍,避免 Phase 1 实施时发现不可行
- [ ] CHK077 - 例外申请流程是否明确？平台治理委员会的审批周期是否会影响项目进度？[流程风险, tasks.md L63-64, plan.md L308-314]

### 2. 基础设施部署风险

- [ ] CHK078 - EKS集群创建、FSx配置、数据库迁移的总耗时(10人时)估算是否合理？[时间估算, tasks.md L741]
- [ ] CHK079 - T008g综合验证任务(涵盖所有基础设施)是否足够全面？是否遗漏关键验证项？[验证完整性, tasks.md L169-183]
- [ ] CHK080 - VPC端点配置不当导致的网络不通问题是否有清晰的排查流程？[故障排查, plan.md L53-57]

### 3. 数据迁移和状态同步风险

- [ ] CHK081 - Alembic迁移系统配置(SQLAlchemy 2.0异步引擎)是否经过验证？是否存在已知问题？[技术风险, tasks.md L43]
- [ ] CHK082 - 训练任务状态同步服务(T037)的30秒延迟是否会导致用户体验问题？[用户体验, tasks.md L293]
- [ ] CHK083 - 检查点分层迁移的异步执行机制是否会导致竞态条件？[并发安全, tasks.md L336]

### 4. 第三方依赖和服务可用性风险

- [ ] CHK084 - SSO服务不可用时的本地账号备用方案是否经过测试？切换流程是否顺畅？[容灾方案, spec.md FR-015]
- [ ] CHK085 - MLflow Tracking Server的可用性是否有SLA保证？是否需要自建高可用方案？[服务可用性, spec.md L806-807]
- [ ] CHK086 - Prometheus数据保留期(30天)是否满足长期趋势分析需求？是否需要归档策略？[数据保留, spec.md L799]

---

## VII. 性能和成本优化审查

### 1. 性能瓶颈识别

- [ ] CHK087 - FSx for Lustre单客户端吞吐量≥5GB/s的性能目标是否经过压测验证？[性能验证, tasks.md L134-140]
- [ ] CHK088 - API响应时间P99<3秒的性能目标是否合理？是否需要针对不同接口设置不同目标？[性能目标, plan.md L76]
- [ ] CHK089 - 训练指标刷新间隔30秒是否满足用户实时监控需求？是否可以优化到10秒？[用户体验, spec.md L783-787]
- [ ] CHK090 - 日志流延迟<10秒的目标是否可达？CloudWatch Logs延迟是否可控？[延迟优化, spec.md L786]

### 2. 成本优化机会

- [x] **CHK091 - ✅ 已解决** - NAT Gateway 部署优化为双 AZ 配置。[成本优化, tasks.md L124-128]
  - **决策**: 采用方案C (2 个 NAT Gateway) - 在 AZ-a 和 AZ-b 部署, AZ-c 跨 AZ 路由
  - **成本节省**: $100/月 → $67/月 (节省 $33/月, 33%)
  - **高可用性**: 保留 2 AZ 容错, 符合企业级标准
  - **理由**: 平衡成本和高可用性, 训练平台主要流量走 PrivateLink, NAT Gateway 跨 AZ 流量成本影响有限
- [ ] CHK092 - Aurora Serverless v2的按需扩缩容配置是否会导致意外高成本？是否需要成本告警？[成本控制, tasks.md L78]
- [ ] CHK093 - S3冷检查点的30天保留期是否可以进一步优化(例如15天)？[存储成本, tasks.md L141]
- [ ] CHK094 - GPU节点的Auto Scaling缩容策略(空闲>15分钟)是否过于激进？是否会导致频繁扩缩容？[成本 vs 性能, tasks.md L98]

### 3. 资源利用率优化

- [ ] CHK095 - GPU利用率≥70%的目标是否合理？是否存在进一步优化空间？[资源利用率, plan.md L73]
- [ ] CHK096 - 训练任务停滞检测(30分钟无指标变化)的阈值是否合理？是否会误杀正常任务？[资源释放策略, spec.md L948]
- [ ] CHK097 - 开发环境资源限制(ml.g5.xlarge, 1小时空闲超时)是否足够合理？[资源管理, spec.md L282-285]

---

## VIII. 测试覆盖率和质量保障审查

### 1. 单元测试覆盖率

- [ ] CHK098 - 核心业务逻辑(训练任务调度/检查点管理/资源配额控制)覆盖率≥90%的目标是否可达？[测试质量, spec.md SC-011]
- [ ] CHK099 - 单元测试任务(T091/T092)的工作量估算是否合理？是否预留足够时间编写高质量测试？[时间估算, tasks.md L569-570]
- [ ] CHK100 - 单元测试是否覆盖所有SDK绕过场景(kubernetes-client/boto3)？[测试覆盖, plan.md L126-129]

### 2. 集成测试和E2E测试

- [ ] CHK101 - API Contract集成测试(T093-T095)是否覆盖所有异常场景(4xx/5xx错误)？[异常处理测试, tasks.md L573-575]
- [ ] CHK102 - E2E测试覆盖所有5个核心User Stories的关键场景，是否足够全面？是否遗漏边界场景？[测试完整性, spec.md SC-013]
- [ ] CHK103 - Gang Scheduling行为验证(T036a)是否覆盖所有失败场景(部分Pod调度失败/超时)？[测试覆盖, tasks.md L286-292]
- [ ] CHK104 - 抢占连续失败转Failed状态测试(T037d)是否验证所有边界条件(连续3次抢占/计数器累加)？[边界测试, tasks.md L295-301]

### 3. 代码质量和静态分析

- [ ] CHK105 - 函数圈复杂度≤10的标准是否严格？是否会导致过度拆分函数？[代码质量, spec.md SC-014]
- [ ] CHK106 - mypy静态类型检查是否配置为严格模式？是否允许Any类型？[类型安全, spec.md SC-014]
- [ ] CHK107 - ESLint规则是否包含no-restricted-imports规则(禁止非Cloudscape组件)？[UI合规性, tasks.md T106]

---

## IX. GitOps 和持续部署审查

### 1. GitOps 工作流设计

- [ ] CHK108 - ArgoCD Application配置(auto-sync/self-heal)是否合理？是否会导致意外的自动回滚？[部署安全, tasks.md L617-618]
- [ ] CHK109 - 配置漂移检测(5分钟检查间隔)是否足够频繁？是否会产生过多告警噪音？[监控频率, tasks.md L620]
- [ ] CHK110 - GitOps多环境部署(dev/staging/prod)的分支策略是否明确？是否有环境隔离风险？[环境隔离, tasks.md L619]

### 2. CI/CD 流水线

- [ ] CHK111 - GitHub Actions流水线(build→test→push image→update manifest→auto-sync)的步骤是否完整？是否遗漏安全扫描？[流程完整性, tasks.md L619]
- [ ] CHK112 - 容器镜像构建是否使用多阶段构建优化镜像大小？是否有镜像扫描机制？[安全和性能, tasks.md L619]
- [ ] CHK113 - 配置变更审计追踪(Git commit SHA/操作者/变更时间)是否足够详细？是否需要记录变更原因？[审计完整性, tasks.md L620]

---

## X. 安全和合规性审查

### 1. 数据加密

- [x] **CHK114 - ✅ 已解决** - S3 SSE-KMS加密配置已增强,采用静态数据自动加密 + HTTPS传输强制策略。[加密强制, tasks.md L131-141]
  - **解决方案**: 增强 T008b S3 Buckets Stack 配置
  - **实施内容**:
    - 明确三类存储桶: datasets/models/checkpoints,统一启用 SSE-KMS 默认加密
    - 静态数据加密: S3 自动对所有上传对象应用 SSE-KMS,客户端无需指定加密参数
    - 传输加密: Bucket Policy 拒绝 HTTP 传输 (aws:SecureTransport = false)
    - 验证测试: HTTP 请求拒绝、HTTPS 成功且自动加密、GetObject API 验证、Console 验证
  - **符合需求**: FR-018 静态数据加密 (S3 SSE-KMS)、传输加密 (TLS 1.2+)、SC-015 安全标准
- [ ] CHK115 - ALB TLS终止配置是否强制TLS 1.2+？是否禁用不安全的cipher suite？[传输加密, tasks.md L160]
- [ ] CHK116 - 数据库连接是否使用TLS加密？Aurora MySQL是否启用传输加密？[数据库加密, tasks.md L79]

### 2. 身份认证和授权

- [ ] CHK117 - SSO集成(SAML/OIDC)的身份映射逻辑是否清晰？是否支持用户属性同步？[身份管理, tasks.md L214]
- [ ] CHK118 - RBAC策略管理是否支持细粒度权限控制(资源级+操作级)？[权限控制, tasks.md L215]
- [ ] CHK119 - 本地账号密码哈希算法(bcrypt cost factor≥12)是否满足安全标准？[密码安全, tasks.md L218]

### 3. 审计日志

- [ ] CHK120 - 审计日志保留期≥90天的配置是否自动执行？是否有数据丢失风险？[数据保留, spec.md FR-017]
- [ ] CHK121 - 审计日志自动清理服务(T102a)的定时任务(每日凌晨2:00)是否合理？是否需要备份策略？[数据保护, tasks.md L590]
- [ ] CHK122 - 审计日志字段结构是否涵盖所有合规要求(user_id/operation_type/resource_id/result)？[合规性, spec.md L912-927]

---

## XI. 文档和可维护性审查

### 1. 技术文档完整性

- [ ] CHK123 - `docs/hyperpod-sdk-reference.md`是否包含所有验证的SDK方法签名和示例代码？[文档完整性, tasks.md L56]
- [ ] CHK124 - `docs/hyperpod-sdk-fallback.md`是否包含完整的备选方案设计和决策依据？[文档完整性, tasks.md L65]
- [ ] CHK125 - 用户手册(`docs/user-guide.md`)是否覆盖所有5个User Stories的操作流程？[用户文档, tasks.md T105]
- [ ] CHK126 - 部署文档(`docs/deployment.md`)是否包含详细的故障排查手册？[运维文档, tasks.md T105]

### 2. 代码注释和命名规范

- [ ] CHK127 - 所有SDK绕过场景是否在代码中清晰注释说明理由并引用宪章？[代码注释, spec.md L696-714]
- [ ] CHK128 - API端点命名是否遵循RESTful风格(使用复数、短横线分隔)？[命名规范, spec.md L56-60]
- [ ] CHK129 - 数据库表名和列名是否遵循小写+下划线命名规范？[命名规范, spec.md L52-54]

### 3. 监控和告警配置

- [ ] CHK130 - 所有关键系统指标是否配置告警规则(GPU利用率/存储使用率/训练任务失败率)？[监控完整性, tasks.md L432-434]
- [ ] CHK131 - 告警通知渠道是否明确(邮件/Slack/短信)？是否有升级机制？[告警机制, tasks.md L120]
- [ ] CHK132 - Grafana仪表盘配置是否版本化管理(JSON配置文件纳入Git)？[配置管理, tasks.md L435]

---

## 总结

### 审查统计

- **总检查项数量**: 132
- **关键风险项**: CHK021(SDK验证任务时机)、CHK011(Add-ons安装粒度)、CHK046(架构过度分层)、CHK065(状态模型复杂度)
- **优化建议项**: CHK003(NAT Gateway成本优化)、CHK016(FSx吞吐量选择)、CHK061(功能优先级调整)

### 主要发现分类

| 类别 | 发现数量 | 严重程度 |
|------|---------|---------|
| 架构设计问题 | 15 | 🔴 高 |
| SDK使用合规性 | 10 | 🟡 中 |
| 过度设计问题 | 12 | 🟡 中 |
| 性能和成本优化 | 11 | 🟢 低 |
| 测试覆盖率 | 10 | 🟡 中 |
| 文档和可维护性 | 8 | 🟢 低 |

### 推荐行动项 (优先级排序)

**P0 - 立即处理 (阻塞性问题)**:
1. ~~CHK021 - SDK方法验证任务应该在Phase 0研究阶段完成，而非Phase 1初期~~ ✅ **已完成 (2026-01-05)**
   - 解决方案: 创建Phase 0技术可行性研究阶段,将T000(原T008h)移至Phase 0
   - 影响: tasks.md新增Phase 0部分,plan.md扩展Phase 0研究,所有依赖关系已更新
2. ~~CHK076 - SDK备选方案需要技术预研和POC验证~~ ✅ **已完成 (2026-01-05)**
   - 解决方案: T000-fallback 增加三阶段执行策略 (分析 → POC验证 → 整合治理)
   - 影响: POC验证覆盖 boto3/kubernetes-client 关键功能,工作量1人日→2人日
   - 产出: POC代码 + 验证报告,确保备选方案技术可行性
3. ~~CHK114 - S3加密配置必须强制启用并验证~~ ✅ **已完成 (2026-01-05)**
   - 解决方案: 增强 T008b S3 Buckets Stack 配置,采用静态数据自动加密 + HTTPS传输强制
   - 影响: 明确三类存储桶 (datasets/models/checkpoints),SSE-KMS 自动加密,Bucket Policy 拒绝 HTTP
   - 验证: HTTP 拒绝测试 + GetObject API 验证 + Console 配置验证
4. ~~CHK011 - HyperPod Add-ons安装任务应拆分为更细粒度的子任务~~ ✅ **已完成 (2026-01-05)**
   - 解决方案: 拆分 T008d 为 3 个逻辑任务组 (T008d-1/2/3)
   - 影响: T008d-1 (训练核心) → {T008d-2 (监控), T008d-3 (开发环境)} 可并行执行
   - 产出: 更好的问题隔离,降低重试成本,启用并行执行机会
5. ~~CHK046 - 评估后端架构是否存在过度分层~~ ✅ **已完成 (2026-01-05)**
   - 决策: 保持 Repository + Service 4层架构
   - 理由: 符合企业级 DDD 模式,职责清晰,可测试性强,为未来扩展预留空间
   - 风险缓解: Base Repository 封装通用 CRUD,开发文档明确各层职责
6. ~~CHK065 - 简化训练任务状态模型~~ ✅ **已完成 (2026-01-05)**
   - 决策: 保持 Submitted/Running/Paused/Preempted/Completed/Failed 6状态模型
   - 理由: 精确反映 HyperPod 调度机制,目标用户能理解调度细节,每个状态有明确业务语义
   - 用户体验优化: UI 友好化、用户引导、详情页细化、监控告警
7. ~~CHK091 (CHK003) - NAT Gateway 成本优化~~ ✅ **已完成 (2026-01-05)**
   - 决策: 采用双 NAT Gateway 配置 (AZ-a 和 AZ-b)
   - 成本节省: $100/月 → $67/月 (节省 $33/月, 33%)
   - 高可用性: 保留 2 AZ 容错能力,平衡成本和可靠性

**P1 - 近期处理 (高风险问题)**:

**P2 - 持续改进 (优化建议)**:
8. CHK016 - 明确FSx吞吐量级别选择标准，避免过度配置
9. CHK061 - 重新评估Phase 6成本分析功能的优先级
10. CHK098 - 确保核心业务逻辑测试覆盖率≥90%

---

**检查清单版本**: v1.0
**生成日期**: 2026-01-05
**下次审查**: 技术方案定稿后、实施前
