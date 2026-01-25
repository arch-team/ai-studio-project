# Feature Specification: AI 训练平台规范完整性改进

**Feature Branch**: `002-spec-completeness`
**Created**: 2026-01-25
**Status**: Draft
**Input**: 基于 `cc-doc/plans/2026-01-25-spec-md-完整性改进计划.md` 生成的需求迭代，补充 9 项关键功能和边界情况

## 概述

本迭代对现有 AI 训练平台规范 (`specs/001-ai-training-platform/spec.md`) 进行完整性补充，涵盖角色体系、危险操作确认机制、API 限流策略、通知机制、数据集生命周期管理、Space 边界情况、模型审批流程、训练任务工作流编排、API 错误码标准等 9 项内容。

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 通知机制 (Priority: P1)

平台管理员和算法工程师需要及时了解训练任务状态变更、预算预警、存储容量告警等关键事件，通过邮件、站内信或 Webhook 接收通知。

**Why this priority**: 通知机制直接影响用户对平台事件的感知和响应速度，是用户体验的核心功能。

**Independent Test**: 可通过触发训练任务完成事件，验证用户收到邮件和站内信通知。

**Acceptance Scenarios**:

1. **Given** 用户订阅了训练任务状态通知, **When** 训练任务完成或失败, **Then** 用户在 5 分钟内收到邮件和站内信通知
2. **Given** 项目配额使用率达到 80%, **When** 系统检测到阈值, **Then** 项目成员收到预算预警邮件
3. **Given** 用户配置了 Webhook 回调 URL, **When** 任务状态变更, **Then** 系统向该 URL 发送 POST 请求
4. **Given** 用户在通知设置中关闭邮件通知, **When** 事件触发, **Then** 仅发送站内信，不发送邮件

---

### User Story 2 - 危险操作确认机制 (Priority: P1)

用户执行删除训练任务、删除数据集、终止运行中任务等危险操作时，系统需要二次确认防止误操作。

**Why this priority**: 防止数据丢失和误操作是平台安全性的核心要求。

**Independent Test**: 可通过尝试删除训练任务，验证前端弹窗确认和 API confirm 参数要求。

**Acceptance Scenarios**:

1. **Given** 用户点击删除训练任务按钮, **When** 未确认, **Then** 前端显示确认弹窗，展示受影响的检查点列表
2. **Given** API 调用 DELETE /training-jobs/{id} 未携带 confirm=true, **When** 请求到达后端, **Then** 返回 HTTP 428 和 CONFIRMATION_REQUIRED 错误码
3. **Given** 用户确认删除, **When** API 携带 confirm=true, **Then** 成功删除并记录审计日志
4. **Given** 训练任务有关联的检查点, **When** 删除任务, **Then** 确认弹窗显示所有受影响的检查点

---

### User Story 3 - 角色体系和权限控制 (Priority: P1)

不同角色（Platform Admin、Project Owner、Project Member、Project Viewer）拥有不同的操作权限，系统需要正确实施权限控制。

**Why this priority**: 角色权限是多租户平台的安全基础。

**Independent Test**: 可通过不同角色用户登录，验证操作权限是否符合预期。

**Acceptance Scenarios**:

1. **Given** 用户角色为 Project Viewer, **When** 尝试提交训练任务, **Then** 返回 HTTP 403 权限不足
2. **Given** 用户角色为 Project Owner, **When** 管理项目成员, **Then** 可以添加/移除成员、分配角色
3. **Given** 用户角色为 Platform Admin, **When** 访问跨项目资源, **Then** 可以查看所有项目的训练任务和资源使用
4. **Given** 用户角色为 Project Member, **When** 提交训练任务, **Then** 成功提交并仅能管理自己的任务

---

### User Story 4 - 训练任务工作流编排 (Priority: P2)

算法工程师需要定义多个训练任务的依赖关系，形成 DAG 工作流（如：数据预处理 → 模型训练 → 模型评估 → 模型注册）。

**Why this priority**: 工作流编排提升复杂训练流程的自动化程度，但不影响基础训练功能。

**Independent Test**: 可通过创建包含 3 个任务的工作流，验证任务按依赖顺序执行。

**Acceptance Scenarios**:

1. **Given** 用户定义工作流 A → B → C, **When** 提交工作流, **Then** 任务 A 先执行，完成后触发 B，B 完成后触发 C
2. **Given** 工作流任务 B 配置为 on_success 依赖, **When** 任务 A 失败, **Then** 任务 B 不启动，工作流状态为 Failed
3. **Given** 工作流有 on_failure 清理任务, **When** 关键任务失败, **Then** 清理任务自动执行
4. **Given** 用户取消运行中的工作流, **When** 调用 cancel API, **Then** 所有运行中任务被终止

---

### User Story 5 - 模型审批流程 (Priority: P2)

Project Owner 需要审批项目成员注册的模型，确保模型质量符合发布标准。

**Why this priority**: 模型审批是模型治理的重要环节，但不影响基础模型注册功能。

**Independent Test**: 可通过注册模型并提交审批，验证审批人收到通知并能批准/拒绝。

**Acceptance Scenarios**:

1. **Given** Project Member 注册模型, **When** 模型状态为 Registered, **Then** Project Owner 收到审批通知
2. **Given** Project Owner 批准模型, **When** 调用 approve API, **Then** 模型状态变为 Approved，记录审批人和时间
3. **Given** Project Owner 拒绝模型, **When** 调用 reject API 并提供原因, **Then** 模型状态变为 Rejected，用户可查看拒绝原因
4. **Given** 模型被拒绝, **When** 用户修改元数据后重新提交, **Then** 模型状态从 Rejected 变为 Registered

---

### User Story 6 - 数据集生命周期管理 (Priority: P2)

数据工程师需要管理数据集的删除和跨项目共享，确保数据安全和可追溯。

**Why this priority**: 数据集生命周期管理完善数据治理能力。

**Independent Test**: 可通过尝试删除被引用的数据集，验证系统阻止删除并提示冲突。

**Acceptance Scenarios**:

1. **Given** 数据集版本被训练任务引用, **When** 尝试删除该版本, **Then** 返回 HTTP 409，提示存在依赖关系
2. **Given** Project Owner 授权数据集共享, **When** 设置跨项目只读访问, **Then** 被授权项目成员可以读取数据集
3. **Given** 用户执行软删除, **When** 数据集标记为 archived, **Then** 元数据保留供审计，但数据集不可使用
4. **Given** 用户执行硬删除, **When** 携带 confirm=true, **Then** 数据集及存储文件被永久删除

---

### User Story 7 - Space 边界情况处理 (Priority: P3)

平台需要妥善处理 Space 空闲超时、资源抢占、启动失败、存储满载等边界情况。

**Why this priority**: 边界情况处理提升平台稳定性，但属于增强功能。

**Independent Test**: 可通过模拟 Space 空闲超时，验证自动暂停和通知机制。

**Acceptance Scenarios**:

1. **Given** Space 空闲超过 1 小时, **When** 系统检测到, **Then** 自动暂停 Space，保留 EBS 存储，发送站内信通知
2. **Given** Space 被资源抢占, **When** 高优先级任务需要 GPU, **Then** 自动保存工作区，暂停 Space，资源可用时通知用户
3. **Given** Space 启动失败, **When** 重试 2 次仍失败, **Then** 标记为 Failed，记录错误原因，通知用户
4. **Given** Space EBS 存储达到 50GB, **When** 用户创建新文件, **Then** 禁止操作，发送警告通知

---

### User Story 8 - API 限流策略 (Priority: P3)

平台需要实施 API 限流策略，防止服务滥用和 DoS 攻击。

**Why this priority**: 限流是平台安全防护，但不影响正常使用。

**Independent Test**: 可通过短时间大量请求，验证限流返回 429 状态码。

**Acceptance Scenarios**:

1. **Given** 用户请求频率超过限流阈值, **When** 发起 API 请求, **Then** 返回 HTTP 429 Too Many Requests
2. **Given** 限流触发, **When** 响应返回, **Then** 包含 Retry-After 头指示重试时间
3. **Given** 不同 API 端点, **When** 配置不同限流策略, **Then** 写操作限流阈值低于读操作

---

### User Story 9 - API 错误码标准化 (Priority: P3)

前端开发者需要统一的 API 错误响应格式，便于处理各类错误场景。

**Why this priority**: 错误码标准化提升开发体验，属于技术规范。

**Independent Test**: 可通过触发各类错误，验证响应格式符合 RFC 9457 规范。

**Acceptance Scenarios**:

1. **Given** 请求的资源不存在, **When** API 返回错误, **Then** HTTP 404 + ENTITY_NOT_FOUND 错误码
2. **Given** 参数验证失败, **When** API 返回错误, **Then** HTTP 422 + VALIDATION_ERROR + 详细字段错误
3. **Given** 非法状态转换, **When** API 返回错误, **Then** HTTP 409 + INVALID_STATE_TRANSITION + 当前状态和目标状态

---

### Edge Cases

| 场景 | 处理策略 |
|------|---------|
| 通知发送失败（邮件服务不可用） | 记录失败日志，重试 3 次，失败后标记为 failed，不阻塞业务流程 |
| 工作流循环依赖检测 | 提交时校验 DAG 无环，返回 422 + 具体依赖冲突信息 |
| 审批超时（14 天无响应） | 发送提醒通知，不自动批准/拒绝，保持 Registered 状态 |
| 数据集共享权限过期 | 自动撤销访问权限，记录到审计日志 |
| Space 抢占后资源长时间不可用 | 每小时发送通知，提供取消等待选项 |

---

## Requirements *(mandatory)*

### Functional Requirements

#### 角色体系和权限控制 (补充 FR-015)

- **FR-015a**: 系统必须支持混合角色模型：组织级角色（Platform Admin）和项目级角色（Project Owner、Project Member、Project Viewer）
- **FR-015b**: Platform Admin 必须能够进行全局管理、系统配置、用户管理、跨项目资源调配
- **FR-015c**: Project Owner 必须能够管理项目配置、成员管理、资源配额管理、模型审批
- **FR-015d**: Project Member 必须能够提交训练任务、管理数据集、查看监控
- **FR-015e**: Project Viewer 必须仅有只读访问权限（查看任务状态、数据集列表）

#### 危险操作确认机制 (新增)

- **FR-029**: 系统必须对危险操作（删除训练任务、删除数据集、终止运行中任务、删除用户账号、清空资源配额）要求二次确认
- **FR-029a**: 前端必须显示确认弹窗，展示操作影响范围（受影响的资源列表）
- **FR-029b**: API 必须要求 confirm=true 参数，否则返回 HTTP 428 Precondition Required + CONFIRMATION_REQUIRED 错误码

#### API 限流策略 (新增 NFR-002)

- **NFR-002**: 系统必须实现 API 限流策略，防止服务滥用和 DoS 攻击
- **NFR-002a**: 限流触发时必须返回 HTTP 429 + Retry-After 头
- **NFR-002b**: 具体限流阈值在实施阶段根据负载测试结果定义

#### 通知机制 (新增 FR-027)

- **FR-027**: 系统必须提供完整的通知机制，支持多渠道通知和用户订阅配置
- **FR-027a**: 必须支持邮件通知渠道（用于重要事件）
- **FR-027b**: 必须支持站内信渠道（平台内通知中心，支持已读/未读状态）
- **FR-027c**: 应支持 Webhook 渠道（用户配置外部系统回调 URL）
- **FR-027d**: 用户必须能够在个人设置中配置接收哪些类型的通知、通过哪个渠道
- **FR-027e**: 通知类型包括：任务状态变更、预算预警、存储容量告警、训练停滞告警、Space 状态变更

#### 数据集生命周期管理 (补充 FR-005/FR-006)

- **FR-005a**: 有训练任务引用的数据集版本禁止删除，返回 HTTP 409 Conflict
- **FR-005b**: 系统必须支持软删除（标记为 archived），保留元数据供审计
- **FR-005c**: 硬删除需要 Project Owner 权限 + 二次确认
- **FR-006a**: 数据集默认项目级隔离，仅项目成员可访问
- **FR-006b**: 系统必须支持跨项目共享：Project Owner 可授权其他项目只读访问
- **FR-006c**: 共享记录必须包含授权人、被授权项目、权限级别、过期时间

#### Space 边界情况 (补充 FR-012)

- **FR-012a**: Space 空闲超过 1 小时必须自动暂停，保留 EBS 存储，发送站内信通知用户
- **FR-012b**: Space 被资源抢占时必须自动保存工作区状态到 EBS，暂停 Space，释放 GPU，资源可用时通知用户
- **FR-012c**: Space 启动失败必须自动重试 2 次（间隔 30 秒），失败后标记 Failed，记录错误原因，通知用户
- **FR-012d**: Space 存储满载（50GB EBS）必须发送警告通知，禁止新建文件，建议用户清理或申请扩容

#### 模型审批流程 (补充 FR-013)

- **FR-013a**: 系统必须支持模型审批流程：Project Owner 或 Platform Admin 可审批模型
- **FR-013b**: 必须提供批准 API (POST /models/{id}/actions/approve)，状态变为 Approved
- **FR-013c**: 必须提供拒绝 API (POST /models/{id}/actions/reject)，需提供拒绝原因，状态变为 Rejected
- **FR-013d**: 审批记录（审批人、审批时间、审批意见）必须记录到审计日志
- **FR-013e**: 被拒绝的模型用户可修改元数据后重新提交审批（状态从 Rejected 回到 Registered）

#### 训练任务工作流编排 (新增 FR-028)

- **FR-028**: 系统必须支持训练任务工作流编排，允许用户定义任务依赖关系形成 DAG
- **FR-028a**: 必须支持依赖类型：depends_on（前置完成后启动）、on_success（前置成功时触发）、on_failure（前置失败时触发）
- **FR-028b**: 工作流状态必须包括：Pending、Running、Completed、PartiallyFailed、Failed
- **FR-028c**: 必须提供工作流 API：POST /workflows（创建）、GET /workflows/{id}（查询）、POST /workflows/{id}/actions/cancel（取消）
- **FR-028d**: 工作流内所有任务共享提交者的资源配额
- **FR-028e**: 提交时必须验证 DAG 无环，存在循环依赖返回 422

#### API 错误码标准 (补充 API Design Standards)

- **FR-030**: 系统必须采用统一的错误响应格式（基于 RFC 9457 简化版）
- **FR-030a**: 错误响应必须包含：code（错误码）、message（人类可读描述）、details（详细信息）、trace_id（追踪 ID）
- **FR-030b**: 必须实现标准错误码列表：ENTITY_NOT_FOUND (404)、VALIDATION_ERROR (422)、DUPLICATE_ENTITY (409)、INVALID_STATE_TRANSITION (409)、RESOURCE_QUOTA_EXCEEDED (429)、AUTHENTICATION_ERROR (401)、INVALID_CREDENTIALS (401)、TOKEN_EXPIRED (401)、INSUFFICIENT_PERMISSIONS (403)、ACCOUNT_LOCKED (423)、CONFIRMATION_REQUIRED (428)、INTERNAL_ERROR (500)

---

### Key Entities

- **Notification**: 通知记录，包含类型、渠道、接收人、内容、状态（sent/read/failed）、创建时间
- **NotificationPreference**: 用户通知偏好，包含用户 ID、通知类型、启用渠道
- **Workflow**: 工作流定义，包含名称、状态、创建人、任务列表
- **WorkflowTask**: 工作流任务，包含工作流 ID、训练任务 ID、依赖类型、前置任务 ID
- **DatasetShare**: 数据集共享记录，包含数据集 ID、授权人、被授权项目、权限级别、过期时间
- **ModelApproval**: 模型审批记录，包含模型 ID、审批人、审批状态、审批意见、审批时间

---

### Technical Constraints

**SDK Usage** (per Constitution Principle I.B):
- MUST use `sagemaker-hyperpod` Python SDK for all HyperPod interactions
- Verify SDK supports required functionality before design
- Document any SDK limitations requiring alternative approach

**HyperPod Native Components** (per Constitution Principle I.A):
- Use HyperPod Training Operator for distributed training
- Use HyperPod Task Governance for resource management
- Use SageMaker Spaces Add-on for development environments

**Code Quality Standards** (per Constitution Principle X):
- Architecture MUST follow SOLID principles
- MUST prioritize mature SDKs: FastAPI, SQLAlchemy, Pydantic

**UI/UX Consistency** (per Constitution Principle XI):
- MUST use AWS Cloudscape Design System
- MUST align with AWS Console design language

**Clean Architecture** (per Constitution Principle XII):
- Backend code MUST follow four-layer architecture: domain, application, infrastructure, api
- Dependencies flow inward: api → infrastructure → application → domain

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户在 5 分钟内收到训练任务状态变更通知（邮件或站内信）
- **SC-002**: 危险操作确认机制覆盖所有高风险 API 端点（100% 覆盖）
- **SC-003**: 角色权限验证延迟低于 50ms（不影响 API 响应时间）
- **SC-004**: 工作流支持最多 20 个任务节点的 DAG 编排
- **SC-005**: 模型审批流程平均完成时间少于 3 个工作日
- **SC-006**: 数据集跨项目共享操作在 2 分钟内完成
- **SC-007**: Space 边界情况处理（超时暂停、抢占恢复）成功率 99.5%
- **SC-008**: API 限流策略有效阻止 99% 的恶意请求
- **SC-009**: 所有 API 错误响应符合统一格式，前端开发无需特殊处理

---

## Assumptions

1. **邮件发送**: 假设使用 Amazon SES 作为邮件发送服务，已完成域名验证
2. **Webhook 超时**: Webhook 回调超时时间默认 30 秒，失败后重试 3 次
3. **限流阈值**: 默认限流阈值在负载测试后确定，初始值参考行业标准（每用户每分钟 60 次读请求、10 次写请求）
4. **工作流存储**: 工作流定义和状态存储在关系数据库中，与训练任务表关联
5. **审批超时**: 模型审批无自动超时机制，保持人工审批模式
6. **Space 存储**: Space 使用 EBS 持久化存储，默认 50GB 容量上限
