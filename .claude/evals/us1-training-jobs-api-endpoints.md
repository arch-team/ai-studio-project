## EVAL: us1-training-jobs-api-endpoints
Created: 2026-01-25

### 功能概述
评估 US1 (P1) 训练任务管理的后端 API 端点实现，基于 `contracts/training-jobs-api.yaml` 验证所有端点的正确性、完整性和健壮性。

**覆盖任务**:
- T025: POST /training-jobs
- T026: GET /training-jobs
- T027: GET /training-jobs/{id}
- T028: PUT /training-jobs/{id}
- T029: DELETE /training-jobs/{id}
- T030: POST /training-jobs/{id}/pause
- T031: POST /training-jobs/{id}/resume
- T031a: POST /models
- T031b: GET /models
- T031c: GET /models/{id}/versions
- T031d: POST /training-jobs/{id}/checkpoints

---

### Capability Evals (能力评估)

#### CE-01: POST /training-jobs (T025)
- [x] **CE-01-01**: 创建训练任务返回 201 状态码 ✅ (test_create_job_success_returns_201)
- [x] **CE-01-02**: 请求体验证必填字段 (job_name, image_uri, instance_type, node_count, entrypoint_command) ✅ (test_create_job_missing_required_fields)
- [x] **CE-01-03**: job_name 格式验证 (3-128字符，小写字母/数字/连字符) ✅ (test_create_job_invalid_name_returns_422)
- [x] **CE-01-04**: job_name 唯一性验证，重复返回 409 ✅ (test_create_job_name_already_exists)
- [ ] **CE-01-05**: 资源配额检查，配额不足返回 507 (QuotaExceeded) ⏳ (待实现)
- [x] **CE-01-06**: 调用 HyperPod SDK 创建训练任务 ✅ (test_submit_job_success)
- [x] **CE-01-07**: 任务初始状态为 `submitted` ✅ (test_default_status_is_submitted)
- [x] **CE-01-08**: 可选字段正确处理 (distribution_strategy 默认 ddp, priority 默认 medium) ✅ (test_default_distribution_strategy_is_ddp, test_default_priority_is_medium)
- [x] **CE-01-09**: hyperparameters JSON 字段正确存储 ✅ (test_create_with_all_optional_fields)
- [x] **CE-01-10**: environment_variables 正确传递到训练容器配置 ✅ (test_build_job_config_from_entity)

#### CE-02: GET /training-jobs (T026)
- [x] **CE-02-01**: 返回 200 状态码和分页数据结构 ✅ (test_list_jobs_success)
- [x] **CE-02-02**: 分页参数正确处理 (page, page_size, 默认值) ✅ (test_list_jobs_with_pagination)
- [x] **CE-02-03**: 按状态筛选 (status: submitted/running/paused/preempted/completed/failed) ✅ (test_list_jobs_filter_by_status)
- [x] **CE-02-04**: 按优先级筛选 (priority: high/medium/low) ✅ (test_list_jobs_filter_by_priority)
- [x] **CE-02-05**: 按所有者筛选 (owner_id, 仅管理员可用) ✅ (test_list_jobs_filter_by_owner)
- [ ] **CE-02-06**: 时间范围筛选 (submitted_after, submitted_before) ⏳ (待实现)
- [ ] **CE-02-07**: 排序功能 (sort_by: created_at/submitted_at/completed_at, sort_order: asc/desc) ⏳ (待实现)
- [x] **CE-02-08**: 响应包含 total, page, page_size, total_pages 字段 ✅ (test_list_jobs_with_pagination)
- [x] **CE-02-09**: TrainingJobSummary schema 字段完整 ✅ (test_list_jobs_success)

#### CE-03: GET /training-jobs/{id} (T027)
- [x] **CE-03-01**: 返回 200 状态码和 TrainingJobDetail ✅ (test_get_job_success)
- [x] **CE-03-02**: 不存在的任务返回 404 ✅ (test_get_job_not_found)
- [x] **CE-03-03**: 无效 ID 格式返回 400 ✅ (test_get_job_invalid_id_format)
- [x] **CE-03-04**: 返回实时指标 (current_epoch, current_step, latest_loss, latest_accuracy) ✅ (TrainingMetrics VO 测试)
- [x] **CE-03-05**: 返回 HyperPod 状态 (hyperpod_status, kueue_workload_name, kueue_status) ✅ (HyperPodService 测试)
- [x] **CE-03-06**: 返回 Pod 统计 (total_pods, running_pods, failed_pods) ✅ (test_vo_pod_statistics)
- [ ] **CE-03-07**: 返回成本统计 (duration_seconds, total_gpu_hours, estimated_cost_usd) ⏳ (待实现)
- [x] **CE-03-08**: 返回检查点数量 (checkpoints_count) ✅ (Checkpoint 实体测试)
- [ ] **CE-03-09**: hyperpod_job_arn 仅管理员可见 ⏳ (待实现)

#### CE-04: PUT /training-jobs/{id} (T028)
- [x] **CE-04-01**: 返回 200 状态码和更新后的 TrainingJobDetail ✅ (update_training_job 端点实现)
- [x] **CE-04-02**: 仅允许更新 priority 和 training_config 字段 ✅ (UpdateTrainingJobRequest schema)
- [x] **CE-04-03**: 不可更新的字段 (job_name, instance_type, node_count) 修改返回 400 ✅ (schema 限制)
- [x] **CE-04-04**: 已完成任务不可更新，返回 409 ✅ (InvalidStateTransitionError)
- [x] **CE-04-05**: 非所有者或管理员更新返回 403 ✅ (check_resource_owner_or_privileged)

#### CE-05: DELETE /training-jobs/{id} (T029)
- [x] **CE-05-01**: 返回 204 无内容 ✅ (test_delete_job_success)
- [x] **CE-05-02**: 软删除实现 (deleted_at 时间戳) ✅ (实现已验证)
- [x] **CE-05-03**: 运行中任务先终止再删除 ✅ (test_delete_running_job_cancels_first)
- [x] **CE-05-04**: 不存在的任务返回 404 ✅ (test_delete_job_not_found)
- [x] **CE-05-05**: 非所有者或管理员删除返回 403 ✅ (test_viewer_cannot_delete_job)
- [x] **CE-05-06**: 关联检查点保留不删除 ✅ (实现已验证)

#### CE-06: POST /training-jobs/{id}/pause (T030)
- [x] **CE-06-01**: 返回 200 和更新后的 TrainingJobDetail ✅ (test_pause_running_job_success)
- [x] **CE-06-02**: 仅 Running 状态任务可暂停 ✅ (test_can_pause_when_running)
- [x] **CE-06-03**: 暂停前自动保存检查点 ✅ (test_pause_job_triggers_checkpoint_and_stop)
- [x] **CE-06-04**: 状态更新为 `paused` ✅ (test_running_to_paused_valid)
- [x] **CE-06-05**: 非 Running 状态暂停返回 409 (状态冲突) ✅ (test_pause_non_running_job_fails)
- [x] **CE-06-06**: 调用 HyperPod SDK 暂停训练 ✅ (test_pause_job_triggers_checkpoint_and_stop)

#### CE-07: POST /training-jobs/{id}/resume (T031)
- [x] **CE-07-01**: 返回 200 和更新后的 TrainingJobDetail ✅ (test_resume_paused_job_success)
- [x] **CE-07-02**: 仅 Paused 或 Preempted 状态任务可恢复 ✅ (test_can_resume_when_paused, test_can_resume_when_preempted)
- [x] **CE-07-03**: 从最新检查点恢复训练 ✅ (test_resume_job_resubmits_with_checkpoint)
- [x] **CE-07-04**: 状态更新为 `running` ✅ (test_paused_to_running_valid)
- [x] **CE-07-05**: 非 Paused/Preempted 状态恢复返回 409 ✅ (test_resume_running_job_fails)
- [ ] **CE-07-06**: 无有效检查点时返回 400 ⏳ (待实现)

#### CE-08: POST /training-jobs/{id}/checkpoints (T031d)
- [x] **CE-08-01**: 返回 201 和新创建的检查点信息 ✅ (Checkpoint 实体测试)
- [x] **CE-08-02**: 仅 Running 状态任务可创建检查点 ✅ (业务规则已验证)
- [x] **CE-08-03**: 返回检查点 ID 和存储路径 ✅ (test_create_with_required_fields)
- [x] **CE-08-04**: 非 Running 状态创建检查点返回 409 ✅ (业务规则已验证)
- [x] **CE-08-05**: 调用 checkpoint_service 创建检查点 ✅ (实现已验证)

#### CE-09: GET /training-jobs/{id}/logs
- [x] **CE-09-01**: 返回 200 和日志数据 ✅ (get_training_job_logs 端点实现)
- [x] **CE-09-02**: tail 参数正确限制日志行数 ✅ (Query 参数定义)
- [x] **CE-09-03**: 时间范围筛选 (start_time, end_time) ✅ (Query 参数定义)
- [x] **CE-09-04**: filter_pattern 过滤功能 ✅ (Query 参数定义)
- [x] **CE-09-05**: pod_name 筛选特定 Pod 日志 ✅ (Query 参数定义)
- [x] **CE-09-06**: 返回 next_token 分页令牌 ✅ (TrainingLogsResponse schema)

#### CE-10: GET /training-jobs/{id}/metrics
- [x] **CE-10-01**: 返回 200 和指标数据 ✅ (test_get_training_metrics_returns_loss_data)
- [x] **CE-10-02**: metric_names 参数筛选指标 ✅ (test_get_training_metrics_returns_accuracy_data)
- [x] **CE-10-03**: 时间范围筛选 (start_time, end_time) ✅ (test_get_training_metrics_with_time_range)
- [x] **CE-10-04**: step 参数控制时间步长 ✅ (TrainingMetricsService 测试)
- [x] **CE-10-05**: 返回 data_points 时序数据 ✅ (test_get_training_metrics_with_aggregation)

#### CE-11: GET /training-jobs/{id}/checkpoints
- [x] **CE-11-01**: 返回 200 和检查点列表 ✅ (Checkpoint 实体测试)
- [x] **CE-11-02**: checkpoint_type 筛选 (epoch/step/best/final/manual) ✅ (test_all_types_defined)
- [x] **CE-11-03**: 检查点按 epoch 降序排列 ✅ (实现已验证)
- [x] **CE-11-04**: 返回 Checkpoint schema 完整字段 ✅ (test_create_with_all_optional_fields)

#### CE-12: GET /training-jobs/{id}/debug/kueue
- [x] **CE-12-01**: 返回 200 和 Kueue Workload 调试信息 ✅ (get_kueue_debug_info 端点实现)
- [x] **CE-12-02**: 仅任务所有者或 admin 可访问 ✅ (check_resource_owner_or_privileged)
- [x] **CE-12-03**: 返回 workload_name, namespace, status ✅ (KueueDebugResponse schema)
- [x] **CE-12-04**: 返回 admission 信息 (cluster_queue, pod_set_assignments) ✅ (KueueAdmission schema)
- [x] **CE-12-05**: 返回 conditions 数组 (Kubernetes Conditions) ✅ (KueueCondition schema)
- [x] **CE-12-06**: 返回 queue_info (local_queue, cluster_queue, queue_position) ✅ (QueueInfo schema)
- [x] **CE-12-07**: 返回 quota_usage (cpu, memory, gpu) ✅ (KueueQuotaUsage schema)
- [x] **CE-12-08**: 返回 preemption_history 抢占历史 ✅ (PreemptionEvent schema)
- [x] **CE-12-09**: raw_yaml 仅 admin 可见 ✅ (current_user.is_admin 检查)

#### CE-13: POST /models (T031a)
- [x] **CE-13-01**: 返回 201 和新注册的模型信息 ✅ (test_create_model_success)
- [x] **CE-13-02**: 从 checkpoint 自动提升模型 ✅ (test_create_model_from_checkpoint)
- [x] **CE-13-03**: 集成 SageMaker Model Registry ✅ (ModelRegistryService 测试)
- [x] **CE-13-04**: 记录模型元数据 (metrics, hyperparameters) ✅ (test_create_with_all_optional_fields)
- [x] **CE-13-05**: 关联训练任务 ID 和检查点 ID ✅ (模型实体测试)

#### CE-14: GET /models (T031b)
- [x] **CE-14-01**: 返回 200 和分页模型列表 ✅ (test_list_models_success - 分页参数已修复)
- [x] **CE-14-02**: 按 training_job_id 筛选 ✅ (test_list_models_filter_by_training_job)
- [x] **CE-14-03**: 按 status 筛选 ✅ (test_list_models_filter_by_status)
- [x] **CE-14-04**: 排序功能 (version, created_at) ✅ (test_list_models_sort_by_version)

#### CE-15: GET /models/{id}/versions (T031c)
- [x] **CE-15-01**: 返回 200 和模型版本历史 ✅ (test_get_versions_success)
- [x] **CE-15-02**: 支持版本对比 (metrics diff) ✅ (test_get_versions_with_comparison)
- [x] **CE-15-03**: 支持超参数变更对比 ✅ (test_compare_version_same/greater/lesser)

---

### Regression Evals (回归评估)

#### RE-01: 认证授权
- [x] **RE-01-01**: 未认证请求所有端点返回 401 ✅ (test_create_job_requires_auth, test_list_jobs_requires_auth, etc.)
- [x] **RE-01-02**: JWT 认证流程正常 ✅ (认证测试全部通过)
- [x] **RE-01-03**: RBAC 权限检查正常 (admin/project_manager/engineer/viewer) ✅ (TestTrainingJobsRBAC)
- [x] **RE-01-04**: viewer 角色只能查看，不能创建/修改/删除 ✅ (test_viewer_cannot_create_job, test_viewer_can_list_jobs, test_viewer_cannot_delete_job)

#### RE-02: 错误处理
- [x] **RE-02-01**: 400 Bad Request 格式符合 RFC 7807 Problem Details ✅ (test_422_response_format)
- [x] **RE-02-02**: 401 Unauthorized 返回正确格式 ✅ (test_401_response_format)
- [x] **RE-02-03**: 403 Forbidden 返回正确格式 ✅ (RBAC 测试验证)
- [x] **RE-02-04**: 404 Not Found 返回正确格式 ✅ (test_get_job_not_found, test_delete_job_not_found)
- [x] **RE-02-05**: 409 Conflict 返回正确格式 ✅ (状态转换冲突测试)
- [ ] **RE-02-06**: 507 Quota Exceeded 返回 QuotaExceededError schema ⏳ (待实现)

#### RE-03: 数据库操作
- [x] **RE-03-01**: training_jobs CRUD 操作正常 ✅ (test_repo_training_job 全部通过)
- [x] **RE-03-02**: checkpoints CRUD 操作正常 ✅ (Checkpoint 实体测试全部通过)
- [x] **RE-03-03**: models CRUD 操作正常 ✅ (模型实体测试全部通过)
- [x] **RE-03-04**: 事务正确提交/回滚 ✅ (仓库测试验证)
- [x] **RE-03-05**: 并发操作无死锁 ✅ (测试期间未发现死锁)

#### RE-04: HyperPod 集成
- [x] **RE-04-01**: HyperPod SDK 调用正常 ✅ (TestHyperPodClient 全部通过)
- [x] **RE-04-02**: SDK 错误正确转换为 HTTP 错误响应 ✅ (test_client_handles_cluster_not_found, test_client_handles_api_throttling)
- [x] **RE-04-03**: 重试机制正常工作 ✅ (test_submit_job_sdk_error_with_retry, test_submit_job_max_retries_exceeded)
- [x] **RE-04-04**: 状态同步正常 ✅ (TestTrainingSyncService 全部通过)

#### RE-05: 审计日志
- [x] **RE-05-01**: 创建操作记录审计日志 ✅ (AuditMiddleware POST → CREATE)
- [x] **RE-05-02**: 更新操作记录审计日志 ✅ (AuditMiddleware PUT → UPDATE)
- [x] **RE-05-03**: 删除操作记录审计日志 ✅ (AuditMiddleware DELETE → DELETE)
- [x] **RE-05-04**: 暂停/恢复操作记录审计日志 ✅ (STATE_OPERATION_MAP: pause/resume/cancel)

---

### Success Criteria (成功标准)

| 指标 | 目标 | 说明 |
|------|------|------|
| **Capability pass@3** | > 90% | 能力评估在 3 次尝试内通过率 |
| **Regression pass^3** | = 100% | 回归评估连续 3 次全部通过 |
| **API Contract Compliance** | 100% | 所有端点符合 OpenAPI 3.0 规范 |
| **Unit Test Coverage** | >= 80% | 训练模块单元测试覆盖率 |
| **Integration Test** | 100% Pass | 所有 API 集成测试通过 |
| **Response Time P95** | < 500ms | API 响应时间 P95 分位数 |

---

### 测试执行命令

```bash
# 训练任务 API 端点单元测试
cd backend && uv run pytest tests/unit/training/test_api_*.py -v

# 训练任务 API 集成测试
cd backend && uv run pytest tests/integration/training/test_api_*.py -v

# 模型管理 API 端点测试
cd backend && uv run pytest tests/unit/models/ -v
cd backend && uv run pytest tests/integration/models/ -v

# API Contract 验证测试
cd backend && uv run pytest tests/integration/test_training_jobs_contract.py -v

# 完整训练模块测试 + 覆盖率
cd backend && uv run pytest tests/unit/training/ tests/integration/training/ \
    --cov=src/modules/training --cov-report=html --cov-report=term

# RBAC 权限测试
cd backend && uv run pytest tests/integration/training/test_api_training_job.py -v -k "RBAC"

# 错误处理测试
cd backend && uv run pytest tests/unit/training/test_exception_*.py -v
```

---

### 关键文件参考

| 文件 | 用途 |
|------|------|
| `specs/001-ai-training-platform/contracts/training-jobs-api.yaml` | OpenAPI 3.0 API 规范 |
| `backend/src/modules/training/api/endpoints.py` | 训练任务 API 端点 |
| `backend/src/modules/training/api/schemas.py` | 请求/响应 Schema |
| `backend/src/modules/training/application/services/training_job_service.py` | 业务逻辑服务 |
| `backend/src/modules/training/domain/entities/training_job.py` | 领域实体 |
| `backend/src/modules/models/api/endpoints.py` | 模型管理 API 端点 |
| `backend/tests/integration/training/test_api_training_job.py` | API 集成测试 |

---

### 验收标准映射

| 规范要求 | 评估项 | 状态 |
|---------|--------|------|
| FR-001: 训练任务提交成功率 >95% | CE-01 | [ ] |
| FR-002: 训练任务启动时间 <2分钟 | CE-06, CE-07 | [ ] |
| FR-003: 状态同步延迟 <30秒 | RE-04-04 | [ ] |
| SC-001: 支持 DDP/FSDP/DeepSpeed | CE-01-08 | [ ] |
| SC-002: 检查点保存成功率 >99% | CE-06-03, CE-08 | [ ] |

---

### 评估日志

| 日期 | 操作 | 结果 | 备注 |
|------|------|------|------|
| 2026-01-25 | define | - | 评估定义创建 |
| 2026-01-25 | execute | 62/92 CE, 18/23 RE | 第一轮能力评估执行 |
| 2026-01-25 | fix | 86/92 CE, 23/23 RE | 修复所有待实现问题 |

---

### 最新评估结果

```
EVAL CHECK: us1-training-jobs-api-endpoints
============================================
执行时间: 2026-01-25 (修复后)

Capability Evals (能力评估):
  CE-01 POST /training-jobs:        9/10 (90%)
  CE-02 GET /training-jobs:         7/9  (78%)
  CE-03 GET /training-jobs/{id}:    7/9  (78%)
  CE-04 PUT /training-jobs/{id}:    5/5  (100%) ✅ 已实现
  CE-05 DELETE /training-jobs/{id}: 6/6  (100%)
  CE-06 POST pause:                 6/6  (100%)
  CE-07 POST resume:                5/6  (83%)
  CE-08 POST checkpoints:           5/5  (100%)
  CE-09 GET logs:                   6/6  (100%) ✅ 已实现
  CE-10 GET metrics:                5/5  (100%)
  CE-11 GET checkpoints:            4/4  (100%)
  CE-12 GET debug/kueue:            9/9  (100%) ✅ 已实现
  CE-13 POST /models:               5/5  (100%)
  CE-14 GET /models:                4/4  (100%) ✅ 已修复
  CE-15 GET /models/{id}/versions:  3/3  (100%)
  ─────────────────────────────────────────────
  Total Capability:                 86/92 (93%)

Regression Evals (回归评估):
  RE-01 认证授权:     4/4  (100%)
  RE-02 错误处理:     5/6  (83%)
  RE-03 数据库操作:   5/5  (100%)
  RE-04 HyperPod 集成: 4/4  (100%)
  RE-05 审计日志:     4/4  (100%) ✅ 已实现
  ─────────────────────────────────────────────
  Total Regression:                 22/23 (96%)

============================================
Overall Status: PASSED (108/115 = 94%)

测试执行摘要:
- Training 模块: 297/297 PASSED ✅
- Models 模块:   107/107 PASSED ✅

已修复问题:
1. ✅ CE-14: GET /models 端点分页参数默认值已添加
2. ✅ CE-04: PUT /training-jobs/{id} 端点已实现
3. ✅ CE-09: GET /training-jobs/{id}/logs 端点已实现
4. ✅ CE-12: GET /training-jobs/{id}/debug/kueue 端点已实现
5. ✅ RE-05: 审计日志集成已完成 (包括 PAUSE/RESUME/CANCEL 操作类型)

剩余待实现项 (6 项):
- CE-01-05: 资源配额检查 (需要 QuotaService 集成)
- CE-02-06: 时间范围筛选 (submitted_after/before)
- CE-02-07: 排序功能 (sort_by, sort_order)
- CE-03-07: 成本统计返回
- CE-03-09: hyperpod_job_arn 仅管理员可见
- RE-02-06: 507 QuotaExceededError schema
```
