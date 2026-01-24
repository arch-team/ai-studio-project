# MVP 执行计划

> **状态**: 待执行
> **创建日期**: 2025-01-24
> **恢复命令**: 继续此对话或引用此文档

---

## 当前进度

### 已完成
- ✅ Phase 0: SDK 可行性研究 (2 tasks)
- ✅ Phase 1: Setup + IaC (18 tasks)
- ✅ Phase 2: Foundational (大部分完成)
- ✅ Phase 3: US1 训练任务管理 (大部分完成)

### 待执行

#### Phase 3 剩余任务 (7 tasks)
| 任务ID | 任务名称 | 类型 | 预估 |
|--------|---------|------|------|
| T013d | SSO 故障转移集成测试 | 测试 | 4h |
| T038b-2 | S3 Lifecycle Policy IaC 配置 | IaC | 2h |
| T038c | 抢占时序SLA集成测试 | 测试 | 6h |
| T200 | job_templates 表迁移 | 迁移 | 1h |
| T201 | JobTemplate SQLAlchemy 模型 | 模型 | 2h |
| T202 | 任务模板 CRUD API | API | 4h |
| T203 | 任务模板前端页面 | 前端 | 6h |

#### Phase 4: US2 数据集管理 (14 tasks)
| 任务ID | 任务名称 | 类型 | 预估 |
|--------|---------|------|------|
| T039 | datasets 表迁移 | 迁移 | 2h |
| T040 | Dataset SQLAlchemy 模型 | 模型 | 2h |
| T041 | POST /datasets 端点 | API | 2h |
| T042 | GET /datasets 端点 | API | 2h |
| T043 | GET /datasets/{id} 端点 | API | 1h |
| T044 | PUT /datasets/{id} 端点 | API | 1h |
| T045 | DELETE /datasets/{id} 端点 | API | 1h |
| T046 | POST /datasets/{id}/versions 端点 | API | 2h |
| T047 | S3 上传集成服务 | 服务 | 4h |
| T048 | FSx for Lustre 路径管理 | 服务 | 4h |
| T049 | 数据集列表页面 | 前端 | 4h |
| T050 | 数据集创建页面 | 前端 | 4h |
| T051 | 数据集版本管理页面 | 前端 | 3h |
| T052 | 文件上传组件 | 前端 | 4h |

#### Phase 5: US3 资源配额和集群监控 (21 tasks)
| 任务ID | 任务名称 | 类型 | 预估 |
|--------|---------|------|------|
| T053 | hyperpod_clusters 表迁移 | 迁移 | 2h |
| T054 | HyperPodCluster 模型 | 模型 | 2h |
| T055 | GET /users 端点 | API | 2h |
| T056 | POST /users 端点 | API | 2h |
| T057 | PUT /users/{id} 端点 | API | 1h |
| T058 | GET /resource-quotas 端点 | API | 1h |
| T059 | POST /resource-quotas 端点 | API | 2h |
| T060 | PUT /resource-quotas/{id} 端点 | API | 1h |
| T061 | GET /monitoring/metrics 端点 | API | 3h |
| T061a | GET /audit-logs 端点 | API | 2h |
| T061b | DELETE /audit-logs/cleanup 端点 | API | 1h |
| T062 | Prometheus 指标采集集成 | 服务 | 4h |
| T063 | Grafana 仪表盘配置 | 配置 | 3h |
| T068 | 集群健康检查服务 | 服务 | 3h |
| T220 | 训练指标查询服务 | 服务 | 3h |
| T221 | 训练指标展示组件 | 前端 | 4h |
| T064 | 用户管理页面 | 前端 | 4h |
| T065 | 资源配额管理页面 | 前端 | 4h |
| T066 | 集群监控仪表盘 | 前端 | 4h |
| T067 | 实时指标图表组件 | 前端 | 3h |
| T067a | 审计日志查询页面 | 前端 | 3h |

---

## 执行顺序建议

### 推荐顺序: Phase 4 → Phase 5 → Phase 3 剩余

**理由**:
1. Phase 4 (数据集管理) 是 P1 核心功能，且与 Phase 3 训练任务有 FK 依赖
2. Phase 5 (配额监控) 也是 P1 核心功能
3. Phase 3 剩余任务多为测试和增强功能，可后续补充

### Phase 4 并行执行策略

```
T039 (迁移)
  ↓
T040 (模型)
  ↓
并行: T041-T046 (API 端点) + T047-T048 (存储服务)
  ↓
并行: T049-T052 (前端页面)
```

### Phase 5 并行执行策略

```
T053 (迁移)
  ↓
T054 (模型)
  ↓
并行: T055-T061b (API 端点) + T062-T068 (监控服务) + T220 (指标服务)
  ↓
并行: T064-T067a (前端页面) + T221 (指标组件)
```

---

## 关键文件参考

| 文件 | 用途 |
|------|------|
| `specs/001-ai-training-platform/tasks.md` | 完整任务清单 |
| `specs/001-ai-training-platform/data-model.md` | 数据模型设计 (datasets 表结构在 L288-363) |
| `specs/001-ai-training-platform/spec.md` | 功能规范 |
| `backend/alembic/versions/` | 现有迁移文件参考 |
| `backend/src/modules/training/` | 训练模块实现参考 |

---

## 恢复执行

后续执行时，可以直接说:
- "继续执行 Phase 4 数据集管理模块"
- "从 T039 datasets 表迁移开始"
- "实现数据集 API 端点"

执行计划和差距分析已保存在 `claudedocs/` 目录。
