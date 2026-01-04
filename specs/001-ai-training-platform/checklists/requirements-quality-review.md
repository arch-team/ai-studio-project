# 需求质量评审检查清单 - 企业级AI训练平台

**Purpose**: 技术评审会议使用，评估功能需求可实现性、非功能需求合理性、架构复杂度
**Created**: 2026-01-04
**Depth**: Standard (40-60 items)
**Audience**: 技术评审会议参与者

---

## 一、功能需求完整性与清晰性 (Functional Requirements)

### 1.1 训练任务管理 (FR-001 ~ FR-004)

- [ ] CHK001 - FR-001 训练模式支持范围是否明确定义了每种模式的资源需求和适用场景量化标准？ [Clarity, Spec §FR-001]
- [ ] CHK002 - FR-001 DataParallel/DDP/FSDP/DeepSpeed ZeRO 的技术约束（互斥规则）是否有验证机制定义？ [Completeness, Gap]
- [ ] CHK003 - FR-001 "SDK 不支持用户请求的训练模式"场景的错误处理是否定义了所有可能的 SDK 版本不兼容情况？ [Coverage, Spec §FR-001]
- [ ] CHK004 - FR-003 Gang Scheduling "60秒调度窗口"是否明确说明了该值的来源（HyperPod 默认值 vs 可配置参数）？ [Clarity, Spec §FR-003]
- [ ] CHK005 - FR-003 重试机制（30s → 60s → 120s 指数退避）是否定义了重试期间任务状态的用户可见性？ [Completeness, Spec §FR-003]
- [ ] CHK006 - FR-004 抢占时序保证"检查点创建超时 5 分钟后强制抢占"与 FR-010 检查点间隔 10-15 分钟是否存在潜在冲突？ [Consistency, Spec §FR-004/FR-010]
- [ ] CHK007 - FR-004 "连续 3 次恢复失败转 Failed"的判定逻辑是否定义了"连续"的时间窗口？ [Ambiguity, Spec §FR-004]

### 1.2 数据集管理 (FR-005 ~ FR-006)

- [ ] CHK008 - FR-005 "大文件数据集上传"是否量化了"大文件"的具体阈值（10GB? 100GB? 1TB?）？ [Clarity, Spec §FR-005]
- [ ] CHK009 - FR-005 断点续传是否定义了续传有效期和临时文件清理策略？ [Completeness, Gap]
- [ ] CHK010 - FR-006 版本比较的"文件列表差异"是否定义了大规模数据集（百万级文件）的性能要求？ [Coverage, Spec §FR-006]

### 1.3 监控与可观测性 (FR-007, FR-014, FR-016)

- [ ] CHK011 - FR-007 双层监控架构（Prometheus + MLflow）的职责边界是否存在指标重叠或数据不一致风险？ [Consistency, Spec §FR-007]
- [ ] CHK012 - FR-007 "训练业务指标刷新 30 秒内在 MLflow UI 可查询"是否考虑了 MLflow 服务不可用的降级方案？ [Coverage, Gap]
- [ ] CHK013 - FR-014 "30 天日志保留期"与 FR-017 "审计日志保留期≥90天"是否存在策略冲突？ [Consistency, Spec §FR-014/FR-017]
- [ ] CHK014 - FR-016 节点健康监控"Deep Health Check"是否定义了具体的检查项目清单和频率？ [Clarity, Spec §FR-016]

### 1.4 检查点与容错 (FR-010 ~ FR-011)

- [ ] CHK015 - FR-010 五种检查点触发场景的优先级和冲突处理规则是否明确定义？ [Completeness, Spec §FR-010]
- [ ] CHK016 - FR-011 分层存储迁移"检查点创建完成后立即异步触发迁移评估"是否定义了异步失败的回滚策略？ [Coverage, Spec §FR-011]
- [ ] CHK017 - FR-011 "所有层均满载则保留最近 1 个检查点"是否定义了"满载"的具体阈值（95%? 99%?）？ [Ambiguity, Spec §FR-011]
- [ ] CHK018 - FR-011 SHA-256 校验和验证在大规模检查点（TB 级别）下的性能影响是否评估？ [Gap, Performance]

### 1.5 认证与安全 (FR-015, FR-017, FR-018)

- [ ] CHK019 - FR-015 SSO 故障转移"连续失败 3 次"的判定是否定义了失败计数的重置条件？ [Completeness, Spec §FR-015]
- [ ] CHK020 - FR-015 "后台每分钟执行 SSO 健康检查"与"SSO 请求超时 5 秒"是否明确了健康检查的超时策略？ [Consistency, Spec §FR-015]
- [ ] CHK021 - FR-017 应用层审计日志字段"request_id"与 AWS CloudTrail 的 request ID 是否可关联？ [Clarity, Spec §FR-017]
- [ ] CHK022 - FR-018 KMS 密钥策略"按资源类型分离密钥"是否定义了具体的密钥分配规则？ [Completeness, Gap]

### 1.6 停滞检测与资源管理 (FR-019 ~ FR-022)

- [ ] CHK023 - FR-022 停滞检测"相对变化率 < 0.1%"是否适用于所有训练场景（如 GAN 的 Loss 震荡）？ [Coverage, Spec §FR-022]
- [ ] CHK024 - FR-022 "30 分钟前值为 0 时使用绝对变化"的特殊处理是否覆盖了所有边界情况？ [Edge Case, Spec §FR-022]
- [ ] CHK025 - FR-020 存储容量监控"95% 满载级别暂停新训练任务提交"是否定义了恢复阈值？ [Completeness, Spec §FR-020]

---

## 二、非功能需求合理性 (Success Criteria)

### 2.1 性能目标可达性

- [ ] CHK026 - SC-001 "GPU 集群整体利用率≥70%"是否基于业界基准或历史数据？该目标在多租户场景下是否现实可达？ [Measurability, Spec §SC-001]
- [ ] CHK027 - SC-002 "模型训练周期缩短≥50%"的基线是什么？是否定义了对比测试方法？ [Clarity, Spec §SC-002]
- [ ] CHK028 - SC-004 "节点故障后 5 分钟内自动恢复"是否考虑了检查点加载时间（TB 级检查点）？ [Consistency, Spec §SC-004]
- [ ] CHK029 - SC-007 "P99 < 3 秒"API 响应时间在 Prometheus/MLflow 查询场景下是否可达（FR-007 定义 P99 <2 秒）？ [Conflict, Spec §SC-007/FR-007]
- [ ] CHK030 - SC-008 "10GB+ 大文件上传成功率 99%"是否定义了网络中断、存储故障等异常场景的处理？ [Coverage, Spec §SC-008]

### 2.2 可用性与可靠性

- [ ] CHK031 - SC-003 "平台可用性 99%（年度）"是否定义了计划内维护窗口的排除规则？ [Clarity, Spec §SC-003]
- [ ] CHK032 - SC-009 "断点续训成功率≥99%"是否定义了"成功"的判定标准（从检查点恢复 vs 训练完成）？ [Ambiguity, Spec §SC-009]
- [ ] CHK033 - SC-010 "100% 关键操作可追溯审计"的"关键操作"范围是否与 FR-017 定义一致？ [Consistency, Spec §SC-010/FR-017]

### 2.3 测试与质量标准

- [ ] CHK034 - SC-011 "关键业务逻辑覆盖率≥90%"是否明确定义了"关键业务逻辑"的范围？ [Completeness, Spec §SC-011]
- [ ] CHK035 - SC-013 "E2E 测试覆盖所有 5 个核心 User Stories"是否包含边缘场景和异常路径？ [Coverage, Spec §SC-013]
- [ ] CHK036 - SC-014 "函数圈复杂度≤10"对于状态机实现（如 Training Job State Model）是否过于严格？ [Clarity, Spec §SC-014]

---

## 三、架构复杂度分析 (Over-Engineering Assessment)

### 3.1 多层存储架构评估

- [ ] CHK037 - 分层检查点存储（NVMe → FSx → S3）三层架构是否必要？是否评估过两层架构（FSx → S3）的可行性？ [Over-Engineering, Spec §FR-011]
- [ ] CHK038 - 检查点迁移策略（热/温/冷）的时间阈值（3/10/72 小时）是否基于实际使用模式数据？ [Assumption, Spec §FR-011]
- [ ] CHK039 - NVMe 本地存储作为"热检查点"层，其容量限制（节点级）是否与多节点分布式训练兼容？ [Gap, Architecture]

### 3.2 双层监控架构评估

- [ ] CHK040 - HyperPod Observability Add-on + SageMaker Managed MLflow 双层监控是否存在功能重叠？ [Over-Engineering, Spec §FR-007]
- [ ] CHK041 - Prometheus Pushgateway 作为"可选备选方案"的定位是否清晰？其维护成本是否评估？ [Clarity, Spec §FR-007]

### 3.3 SDK 集成复杂度评估

- [ ] CHK042 - 同时使用 `sagemaker-hyperpod` SDK + boto3 + kubernetes-client 三种客户端是否增加了不必要的复杂度？ [Over-Engineering, Architecture]
- [ ] CHK043 - "SDK 绕过场景"（Kueue 状态监控、NetworkPolicy 配置、Model Registry）的例外申请流程是否可操作？ [Completeness, Spec §Plan]
- [ ] CHK044 - HyperPod SDK 方法验证任务（T008h）是否应在 Phase 0 研究阶段完成而非 Phase 1？ [Dependency, tasks.md]

### 3.4 状态机复杂度评估

- [ ] CHK045 - Training Job State Model 的 6 种状态 + Kueue 底层状态映射是否过于复杂？用户视角是否需要如此精细的状态？ [Over-Engineering, Spec §State Model]
- [ ] CHK046 - Preempted 状态的"快速路径"（直接 → Running）与"标准路径"（→ Submitted → Running）的选择逻辑是否明确？ [Ambiguity, Spec §State Model]

### 3.5 任务规模评估

- [ ] CHK047 - 153 个任务、312 人时的工作量估算是否合理？是否存在任务粒度过细的问题？ [Over-Engineering, tasks.md]
- [ ] CHK048 - MVP 范围（101 个任务）是否真正体现"最小可行产品"原则？ [Scope, tasks.md]
- [ ] CHK049 - Phase 1 基础设施任务（16 个）中 8 个标记为 [P] 优先级，阻塞依赖是否过重？ [Dependency, tasks.md]

---

## 四、需求一致性与可追溯性 (Traceability)

### 4.1 跨文档一致性

- [ ] CHK050 - spec.md User Story 5 的资源限制（ml.g5.xlarge, 50GB EBS）是否与 tasks.md T079/T081 的实例类型（ml.t3.medium, ml.g4dn.xlarge）一致？ [Conflict, Spec/Tasks]
- [ ] CHK051 - plan.md 定义的"EKS Add-ons 版本要求"是否与 tasks.md T008c/T008d 的实现一致？ [Consistency, Plan/Tasks]
- [ ] CHK052 - spec.md FR-007 定义的监控指标刷新间隔（30 秒）是否与 tasks.md T037 状态同步间隔（30 秒）对齐？ [Consistency, Spec/Tasks]

### 4.2 术语一致性

- [ ] CHK053 - "检查点间隔 10-15 分钟"在 spec.md 和 tasks.md 中是否始终使用相同表述？ [Consistency, Terminology]
- [ ] CHK054 - "三级优先级"（高/中/低）与 Kueue PriorityClass（critical/high/medium）的映射关系是否在所有文档中一致？ [Ambiguity, Terminology]

### 4.3 需求覆盖度

- [ ] CHK055 - Edge Cases 章节列出的 6 个边缘场景是否都有对应的功能需求或任务覆盖？ [Coverage, Gap]
- [ ] CHK056 - Constitution Alignment 章节的 11 个原则是否都有对应的验证机制或检查清单？ [Traceability, Spec]

---

## 五、潜在无法实现的需求 (Implementability Risks)

### 5.1 技术依赖风险

- [ ] CHK057 - `sagemaker-hyperpod` SDK 的 Space 模块是否已正式发布？tasks.md 引用的方法（create_space、delete_space）是否存在？ [Dependency, Gap]
- [ ] CHK058 - HyperPod Training Operator 的 Gang Scheduling 默认配置（60 秒超时、重试策略）是否有官方文档支持？ [Assumption, Spec §FR-003]
- [ ] CHK059 - SageMaker Managed MLflow 在中国区域（如 cn-northwest-1）是否可用？ [Dependency, Gap]

### 5.2 性能目标风险

- [ ] CHK060 - FSx for Lustre "≥5GB/s 单客户端吞吐量"需要 1000 MB/s/TiB + 10 TiB 配置，成本是否评估？ [Assumption, Plan]
- [ ] CHK061 - "IDE 启动时间 <3 分钟"是否考虑了 SageMaker Studio 冷启动场景？ [Measurability, Spec §US5]

### 5.3 运维复杂度风险

- [ ] CHK062 - GitOps 工作流（ArgoCD）+ HyperPod Add-ons + CDK IaC 的多层配置管理是否增加了运维复杂度？ [Over-Engineering, tasks.md]
- [ ] CHK063 - 审计日志自动清理（90 天后删除）是否与合规要求（如等保/SOC2）冲突？ [Assumption, Spec §FR-017]

---

## 检查清单统计

| 类别 | 项目数 | 覆盖范围 |
|------|--------|----------|
| 功能需求完整性与清晰性 | 25 | FR-001 ~ FR-022 |
| 非功能需求合理性 | 11 | SC-001 ~ SC-016 |
| 架构复杂度分析 | 13 | 存储/监控/SDK/状态机/任务规模 |
| 需求一致性与可追溯性 | 7 | 跨文档/术语/覆盖度 |
| 潜在无法实现的需求 | 7 | 技术依赖/性能/运维风险 |
| **总计** | **63** | - |

---

## 评审建议

### 高优先级关注项（建议会议重点讨论）

1. **CHK006** - 抢占检查点超时 vs 定期检查点间隔的潜在冲突
2. **CHK026/CHK027** - GPU 利用率和训练周期优化目标的基线定义
3. **CHK037** - 三层检查点存储架构的必要性评估
4. **CHK047/CHK048** - 153 个任务的规模和 MVP 范围合理性
5. **CHK057** - HyperPod SDK Space 模块的可用性验证

### 建议的会议议程

1. **需求清晰性审查** (20 min) - CHK001~CHK025
2. **性能目标可行性讨论** (15 min) - CHK026~CHK036
3. **架构简化机会识别** (20 min) - CHK037~CHK049
4. **技术风险评估** (15 min) - CHK057~CHK063
5. **行动项确认** (10 min)

---

**检查清单版本**: v1.0
**生成日期**: 2026-01-04
**生成工具**: /speckit.checklist
