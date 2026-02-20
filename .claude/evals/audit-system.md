## EVAL: audit-system
Created: 2026-02-20
Last Check: 2026-02-20 (post-fix)
Module: backend/src/modules/audit/
Phase: 2+5 (Foundational + US3)
Tasks: T010a, T012a, T016b, T061a-T061b, T102a

### Capability Evals

#### 审计日志中间件 (T016b)
- [x] 自动拦截所有 API 请求并记录操作日志
- [x] 正确记录 user_id, operation_type, resource_type, resource_id
- [x] 正确记录 request_data 和 response_data (JSON)
- [x] 正确记录 ip_address 和 user_agent
- [x] 异步写入数据库不阻塞 API 响应
- [x] 审计日志记录 status (success/failed)

#### 审计日志 API (T061a)
- [x] GET /audit-logs 支持分页
- [x] GET /audit-logs 支持按 user_id 过滤
- [x] GET /audit-logs 支持按 operation_type 过滤 (create/update/delete/login/logout)
- [x] GET /audit-logs 支持按 resource_type 过滤 (training_job/dataset/model/user/quota/space)
- [x] GET /audit-logs 支持时间范围过滤
- [x] GET /audit-logs 仅 admin 角色可访问

#### 审计日志清理 (T061b + T102a)
- [x] DELETE /audit-logs/cleanup 清理过期日志 (expires_at < now)
- [x] 清理返回统计 (清理条数、执行耗时、失败记录数)
- [x] 仅 admin 角色可调用清理
- [x] AuditCleanupService 每日 UTC 18:00 (北京 02:00) 自动执行清理
- [x] 清理失败连续 3 天触发 critical 告警
- [x] 保留策略: >= 90 天

#### 领域模型
- [x] AuditLog 实体自动计算 expires_at (created_at + 90 天)
- [x] AuditLog 实体正确关联 User
- [x] 支持所有操作类型和资源类型枚举

### Regression Evals
- [x] 审计中间件不影响 API 性能 (延迟增加 <10ms)
- [x] 审计日志表索引正确创建 (user_id, operation_type, created_at)
- [x] 数据库迁移 (audit_logs 表) 可重复执行
- [x] 清理操作不删除未过期的日志

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 审计日志完整性: 100% API 操作被记录
- FR-017: 保留策略 >= 90 天
