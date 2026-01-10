# IaC 生命周期完整性检查清单

**用途**: 验证 Phase 1 基础设施即代码任务是否涵盖完整的 IaC 项目生命周期

**创建时间**: 2026-01-10

**检查范围**: tasks.md Phase 1: Setup - 项目初始化和基础设施即代码 (T008a - T008g)

**深度级别**: 标准级

**使用场景**: 任务分解验证 | 开发规范审查 | PR 代码评审

---

## 1. 初始化与结构 (Project Initialization & Structure)

### 1.1 项目结构定义
- [ ] CHK001 - 是否定义了 CDK 项目的完整目录结构规范？ [Completeness, Task T008a]
- [ ] CHK002 - 是否明确了 Stack 之间的依赖关系和组织原则？ [Clarity, Task T008a]
- [ ] CHK003 - 是否定义了可复用模块 (Constructs) 的设计规范和存放位置？ [Gap]
- [ ] CHK004 - 是否规定了 CDK 代码与 Kubernetes 清单 (k8s/) 的职责边界？ [Clarity, Task T008a vs T008d]

### 1.2 环境隔离
- [ ] CHK005 - 是否定义了多环境 (dev/staging/prod) 的配置隔离策略？ [Completeness, Task T008a]
- [ ] CHK006 - 是否明确了环境间配置差异的参数化方式 (CDK context vs 环境变量)？ [Clarity, Task T008a]
- [ ] CHK007 - 是否定义了环境特定资源的命名规范 (如 `{project}-{resource}-{env}`)？ [Gap]
- [ ] CHK008 - 是否规定了跨环境部署的隔离验证机制 (防止误操作到生产环境)？ [Gap, Edge Case]

### 1.3 依赖管理
- [ ] CHK009 - 是否定义了 CDK Python 依赖的版本锁定策略 (requirements.txt vs poetry.lock)？ [Gap]
- [ ] CHK010 - 是否明确了 CDK 版本升级的兼容性验证流程？ [Gap]
- [ ] CHK011 - 是否规定了第三方 Construct 库的引入审批流程？ [Gap]

### 1.4 代码规范
- [ ] CHK012 - 是否定义了 IaC 代码的格式化工具和配置 (black, isort, ruff)？ [Gap]
- [ ] CHK013 - 是否规定了 IaC 代码的 Linting 规则 (pylint, mypy)？ [Gap]
- [ ] CHK014 - 是否定义了 Stack/Construct 的命名规范和注释要求？ [Gap]

---

## 2. 状态管理 (State Management)

### 2.1 状态后端配置
- [x] CHK015 - 是否定义了 CDK Bootstrap 的状态存储配置 (CDKToolkit Stack)？ [已覆盖, Task T008a]
- [x] CHK016 - 是否明确了 CloudFormation 状态的存储位置和访问控制？ [已覆盖, Task T008a]
- [x] CHK017 - 是否规定了状态后端 S3 存储桶的加密和版本控制策略？ [已覆盖, Task T008a]

### 2.2 状态锁定机制
- [x] CHK018 - 是否定义了并发部署的锁定机制 (CloudFormation 原生锁定)？ [已覆盖, Task T008a]
- [x] CHK019 - 是否规定了锁定超时和死锁恢复的处理流程？ [已覆盖, Task T008a]

### 2.3 状态安全
- [ ] CHK020 - 是否定义了状态文件中敏感信息的处理策略？ [Gap, Security]
- [ ] CHK021 - 是否规定了状态访问的 IAM 权限最小化原则？ [Gap, Security]
- [ ] CHK022 - 是否明确了状态审计日志的保留和监控要求？ [Gap]

### 2.4 状态备份与恢复
- [ ] CHK023 - 是否定义了 CloudFormation Stack 状态的备份策略？ [Gap]
- [ ] CHK024 - 是否规定了状态损坏或丢失时的恢复流程？ [Gap, Recovery Flow]
- [ ] CHK025 - 是否明确了多环境状态的隔离存储要求？ [Gap]

---

## 3. 变更管理 (Change Management)

### 3.1 Plan/Apply 流程
- [ ] CHK026 - 是否定义了 `cdk diff` 审查的必要性和流程？ [Gap]
- [ ] CHK027 - 是否规定了变更影响评估的标准 (哪些变更需要审批)？ [Gap]
- [ ] CHK028 - 是否明确了 `cdk deploy` 的执行权限和环境限制？ [Gap]
- [ ] CHK029 - 是否定义了部署窗口和变更冻结期的规则？ [Gap]

### 3.2 漂移检测
- [ ] CHK030 - 是否定义了 CloudFormation 漂移检测的执行频率？ [Gap]
- [ ] CHK031 - 是否规定了漂移发现后的处理流程 (告警、修复、记录)？ [Gap]
- [ ] CHK032 - T105e 配置漂移检测仅针对 ArgoCD/K8s 资源，是否涵盖 CDK 管理的 AWS 原生资源漂移？ [Gap, Task T105e]

### 3.3 回滚策略
- [ ] CHK033 - 是否定义了 CDK 部署失败时的自动回滚策略？ [Gap, Critical]
- [ ] CHK034 - 是否规定了手动回滚的操作流程和验证步骤？ [Gap, Recovery Flow]
- [ ] CHK035 - 是否明确了回滚触发条件 (健康检查失败、性能下降等)？ [Gap]
- [ ] CHK036 - 是否定义了不可回滚变更 (如 RDS 引擎升级) 的风险评估流程？ [Gap, Edge Case]

### 3.4 变更审批流程
- [ ] CHK037 - 是否定义了 IaC 代码变更的 PR 审批要求 (至少 N 人审批)？ [Gap]
- [ ] CHK038 - 是否规定了生产环境部署的审批流程和授权人员？ [Gap]
- [ ] CHK039 - 是否明确了紧急变更 (hotfix) 的快速审批通道？ [Gap, Exception Flow]

### 3.5 增量更新策略
- [ ] CHK040 - 是否定义了破坏性变更 (replacement) 的识别和处理策略？ [Gap]
- [ ] CHK041 - 是否规定了蓝绿部署或金丝雀发布的基础设施支持？ [Gap]
- [ ] CHK042 - 是否明确了资源更新顺序的依赖管理 (如先更新 VPC 再更新子网)？ [Clarity, Task T008b]

---

## 4. 安全与合规 (Security & Compliance)

### 4.1 密钥管理
- [ ] CHK043 - T008b S3 SSE-KMS 加密配置是否明确了密钥轮换策略？ [Completeness, Task T008b]
- [ ] CHK044 - 是否定义了 KMS 密钥的访问控制策略 (Key Policy)？ [Clarity, Task T008b]
- [ ] CHK045 - 是否规定了跨账户密钥共享的安全要求？ [Gap]

### 4.2 Secret 管理
- [ ] CHK046 - 是否定义了 IaC 中敏感信息的存储方式 (AWS Secrets Manager vs SSM Parameter Store)？ [Gap, Critical]
- [ ] CHK047 - 是否规定了 Secret 在 CDK 代码中的引用方式 (禁止硬编码)？ [Gap, Security]
- [ ] CHK048 - 是否明确了 Secret 轮换的自动化策略？ [Gap]
- [ ] CHK049 - T006 环境变量模板中的敏感配置 (如 DATABASE_URL) 是否定义了安全传递机制？ [Gap, Task T006]

### 4.3 IAM 策略
- [ ] CHK050 - T008c-3 IAM 角色配置是否遵循最小权限原则的验证方法？ [Measurability, Task T008c-3]
- [ ] CHK051 - 是否定义了 IAM 策略的定期审计和权限回收流程？ [Gap]
- [ ] CHK052 - 是否规定了 CDK 部署角色 (cdk-deploy-role) 的权限边界？ [Gap]
- [ ] CHK053 - 是否明确了服务角色 vs 用户角色的分离原则？ [Clarity, Task T008c-3]

### 4.4 网络安全
- [ ] CHK054 - T008b VPC 配置是否明确了 Network ACL 的配置要求？ [Gap, Task T008b]
- [ ] CHK055 - T008f NetworkPolicy 是否定义了默认拒绝策略的例外审批流程？ [Gap, Task T008f]
- [ ] CHK056 - 是否规定了 VPC 端点的安全组规则最小化原则？ [Clarity, Task T008b]

### 4.5 合规审计
- [ ] CHK057 - 是否定义了 IaC 代码的安全扫描工具 (checkov, cfn-nag, cdk-nag)？ [Gap, Critical]
- [ ] CHK058 - 是否规定了安全扫描在 CI/CD 中的门禁规则 (扫描不通过则阻止合并)？ [Gap]
- [ ] CHK059 - T101a 加密合规性验证是否涵盖所有 IaC 创建的资源？ [Coverage, Task T101a]
- [ ] CHK060 - 是否定义了合规性报告的生成频率和存档要求？ [Gap]

---

## 5. 测试与验证 (Testing & Validation)

### 5.1 静态分析
- [ ] CHK061 - 是否定义了 CDK 代码的类型检查要求 (mypy)？ [Gap]
- [ ] CHK062 - 是否规定了 CloudFormation 模板的语法验证 (`cdk synth` + cfn-lint)？ [Gap]
- [ ] CHK063 - 是否明确了 Kubernetes 清单的静态验证工具 (kubeval, kubeconform)？ [Gap, Task T008d]

### 5.2 单元测试
- [ ] CHK064 - 是否定义了 CDK Stack 的单元测试要求 (assertions 库)？ [Gap, Critical]
- [ ] CHK065 - 是否规定了 IaC 单元测试的覆盖率目标？ [Gap]
- [ ] CHK066 - 是否明确了 Snapshot 测试的使用场景和维护策略？ [Gap]

### 5.3 集成测试
- [ ] CHK067 - T008g 基础设施验证测试是否定义了测试环境的创建和销毁流程？ [Completeness, Task T008g]
- [ ] CHK068 - 是否规定了集成测试的隔离策略 (避免影响其他环境)？ [Gap, Task T008g]
- [ ] CHK069 - 是否明确了集成测试失败时的资源清理机制？ [Gap, Exception Flow]

### 5.4 冒烟测试
- [ ] CHK070 - 是否定义了部署后的冒烟测试检查项 (端点可达、服务健康)？ [Gap]
- [ ] CHK071 - T008g 验证测试是否覆盖所有关键服务的冒烟测试？ [Coverage, Task T008g]
- [ ] CHK072 - 是否规定了冒烟测试的超时和重试策略？ [Gap]

### 5.5 安全扫描
- [ ] CHK073 - 是否定义了 IaC 安全扫描的工具链 (checkov, tfsec 对应的 CDK 工具)？ [Gap]
- [ ] CHK074 - 是否规定了安全扫描规则的自定义和豁免流程？ [Gap]
- [ ] CHK075 - 是否明确了安全漏洞的修复 SLA (Critical: 24h, High: 7d 等)？ [Gap]

### 5.6 性能验证
- [ ] CHK076 - T008e FSx 性能验证是否定义了性能不达标时的升级决策流程？ [Completeness, Task T008e]
- [ ] CHK077 - 是否规定了性能基线的定期重新验证频率？ [Gap, Task T008e]
- [ ] CHK078 - T008g 验证测试是否涵盖网络延迟和吞吐量的性能指标？ [Coverage, Task T008g]

---

## 6. 跨领域关注点 (Cross-Cutting Concerns)

### 6.1 文档要求
- [ ] CHK079 - 是否定义了 IaC 架构决策记录 (ADR) 的模板和存放位置？ [Gap]
- [ ] CHK080 - 是否规定了 Stack 配置参数的文档化要求？ [Gap]
- [ ] CHK081 - 是否明确了 IaC 变更日志 (CHANGELOG) 的维护规范？ [Gap]

### 6.2 可观测性
- [ ] CHK082 - 是否定义了 CDK 部署过程的日志记录和监控？ [Gap]
- [ ] CHK083 - 是否规定了部署失败告警的通知渠道和响应流程？ [Gap]
- [ ] CHK084 - 是否明确了资源标签 (Tags) 的标准化要求 (用于成本分摊、资源归属)？ [Gap]

### 6.3 成本控制
- [ ] CHK085 - 是否定义了 IaC 创建资源的成本估算流程 (`cdk diff` + Infracost)？ [Gap]
- [ ] CHK086 - 是否规定了开发/测试环境的自动销毁策略 (避免资源浪费)？ [Gap]
- [ ] CHK087 - T008b NAT Gateway 成本优化策略是否可量化验证 (预期节省 33%)？ [Measurability, Task T008b]

### 6.4 灾难恢复
- [ ] CHK088 - 是否定义了 IaC 管理资源的灾难恢复策略 (RTO/RPO)？ [Gap, Critical]
- [ ] CHK089 - 是否规定了跨区域灾备的 IaC 部署流程？ [Gap]
- [ ] CHK090 - 是否明确了基础设施重建的自动化程度和手动干预点？ [Gap]

---

## 检查清单统计

| 类别 | 检查项数量 | 已覆盖 | 缺口 |
|------|-----------|--------|------|
| 1. 初始化与结构 | 14 | 4 | 10 |
| 2. 状态管理 | 11 | 0 | 11 |
| 3. 变更管理 | 17 | 1 | 16 |
| 4. 安全与合规 | 18 | 6 | 12 |
| 5. 测试与验证 | 18 | 3 | 15 |
| 6. 跨领域关注点 | 12 | 1 | 11 |
| **总计** | **90** | **15** | **75** |

---

## 关键缺口总结

### 高优先级缺口 (Critical Gaps)
1. **状态管理完全缺失** - 未定义 CDK Bootstrap 配置、状态后端、锁定机制、备份恢复策略
2. **变更管理流程缺失** - 未定义 Plan/Apply 审批流程、回滚策略、漂移检测
3. **IaC 测试策略缺失** - 未定义单元测试、安全扫描工具链、测试覆盖率要求
4. **Secret 管理未明确** - 敏感信息存储和传递机制未定义
5. **灾难恢复策略缺失** - 基础设施 RTO/RPO 和重建流程未定义

### 中优先级缺口 (Important Gaps)
1. **代码规范未定义** - 格式化、Linting、命名规范
2. **依赖管理未明确** - 版本锁定、升级验证流程
3. **合规扫描未集成** - 未定义 cdk-nag/checkov 等工具
4. **成本估算流程缺失** - 未集成 Infracost 或类似工具
5. **文档规范缺失** - ADR、变更日志、参数文档

### 已覆盖的良好实践
1. ✅ 多环境支持 (dev/staging/prod) - Task T008a
2. ✅ S3 加密配置 (SSE-KMS) - Task T008b
3. ✅ IAM 最小权限原则 - Task T008c-3
4. ✅ 基础设施验证测试 - Task T008g
5. ✅ FSx 性能验证 - Task T008e

---

## 建议补充任务

基于检查清单缺口分析，建议在 Phase 1 补充以下任务：

### T008-pre: IaC 基础规范定义 (建议新增)
- 定义 CDK 代码规范 (格式化、Linting、命名规范)
- 定义 CDK Bootstrap 和状态管理策略
- 定义 Secret 管理策略 (Secrets Manager/SSM)
- 配置 cdk-nag 安全扫描规则

### T008h: IaC 变更管理流程 (建议新增)
- 定义 `cdk diff` 审查流程
- 定义回滚策略和触发条件
- 配置 CloudFormation 漂移检测
- 定义变更审批流程

### T008j: IaC 测试框架 (建议新增)
- 配置 CDK assertions 单元测试
- 定义测试覆盖率目标 (建议 ≥70%)
- 集成安全扫描到 CI/CD
- 定义 Snapshot 测试策略

### T008k: IaC 灾难恢复计划 (建议新增)
- 定义基础设施 RTO/RPO 目标
- 文档化重建流程
- 配置跨区域备份策略
