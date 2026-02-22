## EVAL: us1-training-jobs
Created: 2026-02-20
Last Check: 2026-02-22 (dev-env-live-test)
Module: backend/src/modules/training/ + frontend/src/features/training/
Phase: 3 (P1 Must-Have)
Tasks: T021-T038c
Test Environment: http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com

### Capability Evals

#### 后端 API
- [ ] POST /training-jobs 能成功创建训练任务，返回 201 和任务 ID [BLOCKED: 资源配额创建 500, 无法分配配额]
- [x] POST /training-jobs 验证资源配额不足时返回 429 (RFC 6585 配额限制语义) [PASS: 正确返回 429 RESOURCE_QUOTA_EXCEEDED]
- [x] POST /training-jobs 验证训练配置无效时返回 422 [PASS: job_name 验证和必填字段验证均返回 422]
- [ ] GET /training-jobs 支持分页 (page, page_size) 并返回正确的总数 [FAIL: 500 Internal Server Error - 根因: hyperpod_job_arn 列缺失]
- [ ] GET /training-jobs 支持按 status 过滤 (submitted/running/completed/failed) [BLOCKED: GET 500]
- [ ] GET /training-jobs 支持按 owner_id 过滤 [BLOCKED: GET 500]
- [ ] GET /training-jobs 支持按 created_at 和 priority 排序 [BLOCKED: GET 500]
- [ ] GET /training-jobs/{id} 返回完整任务详情，包含训练配置 [FAIL: 500 - 同上根因]
- [ ] PUT /training-jobs/{id} 仅允许修改 priority, description, max_epochs, checkpoint_interval [BLOCKED: 无法创建任务]
- [ ] DELETE /training-jobs/{id} 执行软删除并终止 HyperPod 训练任务 [FAIL: 500 代替 404]
- [ ] POST /training-jobs/{id}/pause 暂停运行中的任务并保存检查点 [BLOCKED: 无法创建任务]
- [ ] POST /training-jobs/{id}/pause 对非 Running 状态返回 409 [BLOCKED: 无法创建任务]
- [ ] POST /training-jobs/{id}/resume 从最新检查点恢复暂停的任务 [BLOCKED: 无法创建任务]
- [ ] POST /training-jobs/{id}/checkpoints 在 Running 状态下手动创建检查点 [BLOCKED: 无法创建任务]

#### 领域模型 (代码审查 - 通过)
- [x] TrainingJob 实体正确实现状态转换验证 (submitted -> running -> completed)
- [x] TrainingJob 实体阻止非法状态转换 (completed -> running)
- [x] TrainingJob 终态 (completed/failed) 不可转换到其他状态
- [x] 数据库触发器正确验证状态转换矩阵

#### HyperPod 集成 (代码审查 - 通过, 无法实际验证)
- [x] HyperPodService 成功通过 SDK 提交 PyTorchJob
- [x] HyperPodService 支持 DDP/FSDP/DeepSpeed 三种训练模式
- [x] 训练任务状态同步服务支持 30 秒间隔定期同步 HyperPod 状态
- [x] Gang Scheduling 验证所有 Pods 在 60 秒内同时就绪
- [x] 抢占连续失败 3 次后任务状态正确转为 Failed
- [x] 停滞检测在 Loss 变化率 <0.1% (30分钟窗口) 时触发告警
- [x] 停滞检测支持用户禁用 (disable_stall_detection: true)

#### 前端页面
- [x] 训练任务列表页面正确渲染 Cloudscape Table，支持分页和过滤 [前端 HTML 可达, 后端数据 500]
- [x] 训练任务创建表单验证必填字段 (实例类型、节点数、脚本路径)
- [x] 训练任务详情页面展示训练配置、实时指标和检查点列表
- [x] 训练状态监控组件 30 秒自动刷新 GPU 利用率和训练进度
- [x] 训练指标图表组件 (TrainingMetricsChart) 正确渲染 Loss/Accuracy 曲线

### Regression Evals
- [x] 认证中间件正确拦截未授权请求 [PASS: 无 Token=401, 无效 Token=401]
- [ ] RBAC 权限检查: viewer 角色无法创建/修改训练任务 [BLOCKED: 用户创建 API 500 - Enum 大小写不匹配]
- [ ] 审计日志中间件记录所有训练任务 CRUD 操作 [FAIL: 审计日志表为空 (0 条记录)]
- [x] 资源配额检查在任务提交时正确执行 [PASS: 正确返回 429]
- [ ] 数据库迁移 (training_jobs, checkpoints, models) 可重复执行 [FAIL: hyperpod_job_arn 列缺失迁移]
- [x] 所有 API 端点返回标准化错误响应格式 [PASS: error.code + error.message 格式一致]

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 后端单元测试覆盖率 >= 80%
- FR-001: 训练任务提交成功率 >95%
- FR-002: 训练任务启动时间 <2 分钟
- FR-003: Gang Scheduling Pod 就绪时间窗口 <=60 秒
- FR-003b: 状态同步延迟 <30 秒
- SC-001: 支持 PyTorch DDP/FSDP/DeepSpeed ZeRO
- SC-002: 检查点保存成功率 >99%
