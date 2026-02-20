## EVAL: us3-resource-quotas
Created: 2026-02-20
Last Check: 2026-02-20
Module: backend/src/modules/quotas/ + frontend/src/features/resource-quotas/
Phase: 5 (P1 Must-Have)
Tasks: T012c-T012f, T058-T060, T065

### Capability Evals

#### 后端 API - ResourceQuota
- [x] GET /resource-quotas 返回所有配额模板列表
- [x] POST /resource-quotas 创建配额模板，验证限制值有效性 (CPU, GPU, Memory, Storage)
- [x] PUT /resource-quotas/{id} 更新配额限制并触发用户通知
- [~] 配额检查延迟 <100ms (内存缓存实现，缺 Redis 持久化和性能测试)

#### 后端 API - ResourceLimitConfig (Admin)
- [x] GET /resource-limit-configs 支持分页、按 role 和 project_id 过滤 (仅 admin)
- [x] POST /resource-limit-configs 创建限制配置，防止重复 (同一 role + project_id 唯一)
- [x] PUT /resource-limit-configs/{id} 支持部分更新，变更记录到审计日志
- [x] DELETE /resource-limit-configs/{id} 执行软删除
- [x] 非 admin 角色访问限制配置 API 返回 403

#### 领域模型
- [x] ResourceQuota 实体正确验证配额限制值 (非负数、合理范围)
- [x] ResourceLimitConfig 实体正确关联 User role 和 project_id
- [x] 默认限制查询: 根据 user role + project 查找适用配置
- [x] 训练任务提交时配额检查服务正确执行

#### 前端页面
- [x] 资源配额管理页面 (ResourceQuotasPage) 正确渲染表单和表格
- [x] 配额表单 (QuotaFormModal) 验证输入有效性
- [x] 配额分配统计正确显示已使用/总配额

### Regression Evals
- [x] 配额更新不影响正在运行的训练任务
- [x] 审计日志正确记录所有配额操作
- [x] RBAC 权限: 仅 admin 和 project_manager 可管理配额
- [x] 配额检查在高并发下保持一致性 (无超额分配)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- FR-012: 配额检查延迟 <100ms
