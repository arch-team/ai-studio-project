## EVAL: us1-models
Created: 2026-02-20
Last Check: 2026-02-20
Module: backend/src/modules/models/ + frontend/src/features/models/
Phase: 3 (P1 Must-Have)
Tasks: T022a, T024a, T031a-T031c, T035a-T035e, T038a

### Capability Evals

#### 后端 API
- [x] POST /models 能注册训练完成的模型，自动从 checkpoint 提升
- [x] POST /models 集成 SageMaker Model Registry，生成 registry_arn
- [x] POST /models 记录模型元数据 (metrics, hyperparameters, framework)
- [x] GET /models 支持分页、按 training_job_id 和 status 过滤
- [x] GET /models 支持按 version 和 created_at 排序
- [x] GET /models/{id}/versions 返回模型版本历史
- [x] GET /models/{id}/versions 支持版本对比 (metrics diff, hyperparameter changes)

#### 领域模型
- [x] Model 实体正确关联 TrainingJob 和 Checkpoint
- [x] Model 实体支持语义化版本 (MAJOR.MINOR.PATCH) 比较
- [x] Model 生命周期状态正确转换 (training -> registered -> approved -> deployed -> archived)
- [x] ModelRegistryService 正确调用 SageMaker Model Registry API

#### 前端页面
- [x] 模型列表页面 (ModelListPage) 正确渲染表格，支持分页/过滤/排序
- [x] 模型详情页面 (ModelDetailPage) 展示元数据和关联训练任务
- [x] 模型版本管理页面 (ModelVersionsPage) 展示版本历史
- [x] 模型版本对比组件 (ModelMetricsCompare) 正确可视化 metrics diff
- [x] Registry 同步状态组件 (RegistrySyncStatus) 正确显示同步状态

### Regression Evals
- [x] 模型注册不影响训练任务正常运行
- [x] SageMaker Model Registry 集成失败时返回明确错误信息
- [x] 模型删除 (软删除) 不影响关联的训练任务和检查点记录
- [x] 认证和权限检查正确应用于所有模型 API 端点

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
