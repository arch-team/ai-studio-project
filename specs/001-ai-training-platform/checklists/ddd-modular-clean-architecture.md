# 架构合规性检查清单 - DDD + Modular Monolith + Clean Architecture

**检查清单类型**: 后端架构规范质量审查
**创建日期**: 2026-01-23
**审查范围**: 依赖方向、模块隔离、DDD 战术模式
**审查目标**: 确保后端代码符合 DDD + Modular Monolith + Clean Architecture 架构规范
**深度级别**: 轻量 (开发参考)

---

## 目的说明

本检查清单验证 `backend/docs/ARCHITECTURE.md` 中定义的架构规范是否在需求和代码中被正确描述和遵循。

**架构三层融合**:
- **DDD (战术设计)**: Entity, Value Object, Aggregate, Domain Event, Repository
- **Modular Monolith**: 垂直切分业务模块，模块间松耦合
- **Clean Architecture**: 依赖倒置，核心业务与外部依赖隔离

---

## I. Clean Architecture 依赖方向

### 1. 分层结构定义

- [x] **CHK001** - Domain 层的独立性是否在架构规范中明确定义? [Completeness, ARCHITECTURE.md §2.1]
  - 是否声明 Domain 层不依赖任何外层?
  - 是否说明 Domain 层只包含 entities/value_objects/repositories 接口/events/exceptions?

- [x] **CHK002** - Application 层的依赖边界是否清晰规定? [Clarity, ARCHITECTURE.md §2.1]
  - 是否明确 Application 层仅依赖 Domain 层?
  - 是否说明 Application 层通过接口依赖 Infrastructure 实现?

- [x] **CHK003** - API 层到 Application 层的依赖是否被明确约束? [Coverage, ARCHITECTURE.md §2.2]
  - 是否禁止 API 层直接访问 Domain 或 Infrastructure?
  - 是否规定 API 层通过 Application Services 操作业务逻辑?

- [x] **CHK004** - Infrastructure 层实现接口的职责是否清晰? [Clarity, ARCHITECTURE.md §2.2]
  - 是否说明 Infrastructure 层实现 Domain 定义的 Repository 接口?
  - 是否说明 Infrastructure 层实现 Application 定义的外部服务接口?

### 2. 依赖倒置原则 (DIP)

- [x] **CHK005** - Repository 接口与实现的分离是否被规定? [Completeness, ARCHITECTURE.md §2.1]
  - 接口是否定义在 `domain/repositories/`?
  - 实现是否放置在 `infrastructure/repositories/`?

- [x] **CHK006** - 外部服务适配器的抽象是否被要求? [Coverage, ARCHITECTURE.md §2.1]
  - 是否要求通过 `application/interfaces/` 定义外部服务接口?
  - 是否要求在 `infrastructure/` 实现具体适配器?

- [x] **CHK007** - 依赖注入机制是否被规范? [Clarity, ARCHITECTURE.md §7]
  - 是否定义了 5 层依赖注入链?
  - 是否说明通过 FastAPI Depends 实现依赖注入?

---

## II. Modular Monolith 模块隔离

### 1. 模块间依赖规则 (R1-R4)

- [x] **CHK008** - R1 规则 (Domain 层绝对隔离) 是否被明确定义? [Completeness, ARCHITECTURE.md §3.1]
  - 是否声明 "Module Domain 层 MUST NOT 导入任何其他模块代码"?
  - 是否列出允许的依赖 (仅 shared/domain/*)?

- [x] **CHK009** - R2 规则 (Application 层接口依赖) 是否清晰? [Clarity, ARCHITECTURE.md §3.1]
  - 是否声明 Application 层只能依赖接口，不能依赖实现?
  - 是否禁止直接导入其他模块的 Service?

- [x] **CHK010** - R3 规则 (模块间通信) 的可选方式是否完整? [Coverage, ARCHITECTURE.md §4.2-4.3]
  - 是否定义 EventBus 用于异步解耦?
  - 是否定义 shared interfaces 用于同步调用?

- [x] **CHK011** - R4 规则 (Auth 模块例外) 的边界是否清晰? [Clarity, ARCHITECTURE.md §3.2.2]
  - 是否明确只有 API 层可以导入 auth 认证依赖?
  - 是否禁止 Domain/Application 层导入 auth?

### 2. 共享内核 (Shared Kernel)

- [x] **CHK012** - shared/domain/ 的职责边界是否被定义? [Completeness, ARCHITECTURE.md §3.2.1]
  - 是否说明 BaseEntity, IRepository, DomainEvent 等基础类型的用途?
  - 是否说明跨模块接口 (如 IQuotaChecker) 的存放位置?

- [x] **CHK013** - shared/infrastructure/ 的内容是否被限定? [Coverage, ARCHITECTURE.md §3.2.1]
  - 是否说明数据库连接、配置管理等共享基础设施的用途?
  - 是否禁止业务逻辑出现在 shared 层?

- [x] **CHK014** - 模块 `__init__.py` 导出规则是否被规范? [Clarity, ARCHITECTURE.md §5.3]
  - 是否要求使用 `__all__` 显式定义公开 API?
  - 是否禁止导出 ORM 模型和仓库实现?

### 3. ORM 模型外键例外

- [x] **CHK015** - ORM 模型跨模块导入的例外是否被说明? [Completeness, ARCHITECTURE.md §3.3.1]
  - 是否说明 `*_model.py` 允许导入其他模块 ORM 模型用于外键?
  - 是否强调这是 SQLAlchemy 技术必要性，非业务依赖?

---

## III. DDD 战术模式

### 1. Entity 实体

- [x] **CHK016** - Entity 的身份标识是否被规范? [Completeness, ARCHITECTURE.md §3.4]
  - 是否要求通过 ID (或 UUID) 区分实体?
  - 是否要求实现 `__eq__` 和 `__hash__` 基于 ID?

- [x] **CHK017** - Entity 的业务逻辑封装是否被要求? [Coverage, ARCHITECTURE.md §3.4]
  - 是否要求状态转换逻辑在 Entity 内部?
  - 是否禁止 Entity 依赖外部服务或数据库?

- [x] **CHK018** - Entity 异常使用规范是否清晰? [Clarity, ARCHITECTURE.md §3.4]
  - 是否要求使用 Domain 异常 (如 InvalidStateTransitionError)?
  - 是否禁止使用 ValueError 等通用异常?

### 2. Value Object 值对象

- [x] **CHK019** - Value Object 的不变性是否被要求? [Completeness, ARCHITECTURE.md §3.4]
  - 是否说明 VO 创建后不可修改?
  - 是否要求通过值比较相等性?

- [x] **CHK020** - Value Object 的验证规则是否被规定? [Coverage, ARCHITECTURE.md §3.4]
  - 是否要求在 VO 创建时进行验证?
  - 是否说明无效值应抛出 ValidationError?

### 3. Repository 仓库

- [x] **CHK021** - Repository 接口的标准方法是否被定义? [Completeness, ARCHITECTURE.md §3.4]
  - 是否定义 get_by_id, create, update, delete 等基础方法?
  - 是否说明复杂查询方法的命名规范?

- [x] **CHK022** - Repository 实现的职责边界是否清晰? [Clarity, ARCHITECTURE.md §3.4]
  - 是否限定 Repository 只负责数据持久化?
  - 是否禁止 Repository 包含业务逻辑?

### 4. Domain Event 域事件

- [x] **CHK023** - Domain Event 的结构是否被规范? [Completeness, ARCHITECTURE.md §3.4]
  - 是否要求继承 DomainEvent 基类?
  - 是否要求包含 event_id 和 occurred_at 字段?

- [x] **CHK024** - 事件发布和订阅机制是否清晰? [Clarity, ARCHITECTURE.md §4.2]
  - 是否说明通过 EventBus.publish_async() 发布事件?
  - 是否说明通过 @event_handler 装饰器订阅事件?

- [x] **CHK025** - 核心域事件清单是否完整? [Coverage, ARCHITECTURE.md §4.4]
  - 是否列出各模块的关键事件?
  - 是否说明事件的触发场景和订阅者?

---

## IV. 模块结构一致性

### 1. 目录结构规范

- [x] **CHK026** - 模块目录结构模板是否被定义? [Completeness, ARCHITECTURE.md §5.1]
  - 是否规定 api/, application/, domain/, infrastructure/ 四层结构?
  - 是否说明每个子目录的内容?

- [x] **CHK027** - 文件命名规范是否清晰? [Clarity, ARCHITECTURE.md §5.2]
  - 是否规定 entity, repository, service, model 的命名模式?
  - 是否保持命名一致性 (如 `_repository.py` vs `_repository_impl.py`)?

### 2. 现有模块一致性

- [x] **CHK028** - 各模块是否遵循统一的目录结构? [Consistency]
  - auth, training, quotas, models, spaces 等模块结构是否一致?
  - 是否存在结构不完整的模块?

- [x] **CHK029** - 各模块的 Domain 层是否完整? [Completeness]
  - 是否包含 entities/, value_objects/, repositories/ 目录?
  - 是否定义 exceptions.py 用于模块异常?

---

## V. 异常处理规范

### 1. 异常继承体系

- [x] **CHK030** - Domain 异常基类是否被定义? [Completeness, ARCHITECTURE.md §6.1]
  - 是否定义 DomainError 作为所有域异常的基类?
  - 是否定义常用子类 (EntityNotFoundError, ValidationError 等)?

- [x] **CHK031** - HTTP 状态码映射是否完整? [Coverage, ARCHITECTURE.md §6.3]
  - 是否说明各异常类型对应的 HTTP 状态码?
  - 映射是否涵盖 404, 409, 422, 429 等常见场景?

### 2. 模块异常定义

- [x] **CHK032** - 模块特定异常的命名是否规范? [Consistency, ARCHITECTURE.md §6.2]
  - 是否遵循 `{Module}Error` 和 `{Entity}NotFoundError` 命名模式?
  - 是否继承自 shared/domain/exceptions?

---

## VI. 自动化合规检查

### 1. 架构测试覆盖

- [x] **CHK033** - 架构合规测试是否覆盖核心规则? [Coverage, tests/architecture/]
  - 是否测试 R1 (Domain 层隔离)?
  - 是否测试 R2 (Application 层接口依赖)?
  - 是否测试 R4 (Auth 模块例外)?

- [x] **CHK034** - 架构测试是否包含在 CI 流程中? [Completeness, ARCHITECTURE.md §8.3]
  - 是否在 CI 中运行 `pytest tests/architecture/`?
  - 测试失败是否阻止合并?

- [x] **CHK035** - ORM 模型外键例外是否被测试正确处理? [Clarity, tests/architecture/]
  - 架构测试是否排除 `*_model.py` 的跨模块导入检查?
  - 是否在测试注释中说明例外原因?

---

## VII. 模块间通信实现

### 1. 事件驱动通信

- [x] **CHK036** - EventBus 实现是否完整? [Completeness, shared/domain/events.py]
  - 是否支持同步和异步事件发布?
  - 是否提供事件订阅装饰器?

- [x] **CHK037** - 事件处理的错误隔离是否被考虑? [Coverage]
  - 单个订阅者失败是否影响其他订阅者?
  - 是否有事件处理失败的重试或补偿机制?

### 2. 共享接口通信

- [x] **CHK038** - 跨模块接口是否定义在正确位置? [Consistency, ARCHITECTURE.md §4.3]
  - IQuotaChecker 等接口是否在 shared/domain/interfaces/?
  - 实现是否在对应模块的 infrastructure/?

- [x] **CHK039** - 接口实现的注入是否被规范? [Clarity, ARCHITECTURE.md §7.4]
  - 是否通过 FastAPI Depends 注入跨模块依赖?
  - 依赖注入链是否清晰?

---

## VIII. 规范文档完整性

### 1. 规范文档组织

- [x] **CHK040** - ARCHITECTURE.md 是否作为架构规范单一真实源? [Completeness]
  - 是否声明本文档为架构规范的权威来源?
  - 其他文档 (CLAUDE.md 等) 是否引用而非重复定义?

- [x] **CHK041** - 快速参考卡片是否涵盖关键规则? [Coverage, ARCHITECTURE.md §9.1]
  - 是否包含允许/禁止的依赖速查?
  - 是否包含模块间通信方式速查?

### 2. 相关文档链接

- [x] **CHK042** - 相关文档引用是否完整? [Completeness, ARCHITECTURE.md §9.2]
  - 是否引用 backend/CLAUDE.md (TDD 工作流)?
  - 是否引用 spec.md (术语标准)?
  - 是否引用 data-model.md (数据库设计)?

---

## 检查清单摘要

| 类别 | 检查项数 | 关键关注点 |
|------|---------|-----------|
| Clean Architecture 依赖方向 | 7 | 分层结构、依赖倒置 |
| Modular Monolith 模块隔离 | 8 | R1-R4 规则、共享内核 |
| DDD 战术模式 | 10 | Entity/VO/Repository/Event |
| 模块结构一致性 | 4 | 目录结构、命名规范 |
| 异常处理规范 | 3 | 异常体系、HTTP 映射 |
| 自动化合规检查 | 3 | 架构测试、CI 集成 |
| 模块间通信实现 | 4 | 事件驱动、共享接口 |
| 规范文档完整性 | 3 | 文档组织、引用链接 |
| **总计** | **42** | |

---

## 检查结果模板

```markdown
### 检查结果

**检查日期**: YYYY-MM-DD
**检查人**: [Name]
**检查范围**: [具体模块或全局]

#### 通过项
- CHK001, CHK002, ...

#### 需改进项
| 编号 | 问题描述 | 建议操作 | 优先级 |
|------|---------|---------|--------|
| CHK0XX | [描述] | [建议] | High/Medium/Low |

#### 总结
[整体评估和下一步行动]
```
