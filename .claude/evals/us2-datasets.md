## EVAL: us2-datasets
Created: 2026-02-20
Module: backend/src/modules/datasets/ + frontend/src/features/datasets/
Phase: 4 (P1 Must-Have)
Tasks: T039-T052

### Capability Evals

#### 后端 API
- [ ] POST /datasets 创建数据集记录，验证元数据完整性
- [ ] POST /datasets 正确设置 status 为 PREPARING
- [ ] GET /datasets 支持分页和多条件过滤 (dataset_type, storage_type, visibility, status)
- [ ] GET /datasets 支持按 created_at 排序
- [ ] GET /datasets 全文搜索 (FULLTEXT) 正确匹配 name 和 description
- [ ] GET /datasets/{id} 返回完整数据集详情，包含访问控制检查
- [ ] GET /datasets/{id} PRIVATE 数据集仅所有者可见
- [ ] PATCH /datasets/{id} 仅允许更新 description, tags, visibility
- [ ] DELETE /datasets/{id} 软删除 (ARCHIVED 状态)，不删除物理存储
- [ ] POST /datasets/{id}/versions 创建新版本，复制元数据和存储路径

#### 领域模型
- [ ] Dataset 实体正确实现版本控制逻辑 (name + version 唯一约束)
- [ ] Dataset 实体支持 6 种数据类型 (IMAGE/TEXT/AUDIO/VIDEO/TABULAR/CUSTOM)
- [ ] Dataset 实体支持 3 种存储类型 (FSX/S3/EFS)
- [ ] Dataset 实体支持 3 种可见性 (PUBLIC/PRIVATE/RESTRICTED)

#### 存储集成
- [ ] S3 分片上传 (multipart upload) 支持 >5GB 文件
- [ ] S3 分片上传计算 MD5 校验和验证数据完整性
- [ ] 断点续传: 上传中断后能从已上传的分片继续
- [ ] 断点续传状态持久化到数据库
- [ ] FSx 同步服务自动将 S3 数据同步到 FSx for Lustre
- [ ] FSx 数据预热逻辑正确执行
- [ ] S3 到 FSx 同步 1TB 数据 <10 分钟

#### 前端页面
- [ ] 数据集列表页面正确渲染，支持搜索/过滤/排序
- [ ] 数据集创建页面支持 drag & drop 文件上传
- [ ] 数据集创建页面显示上传进度条
- [ ] 文件上传组件 (DatasetUploader) 支持取消和重试
- [ ] 数据集版本管理页面显示版本历史时间线
- [ ] useDatasetUpload hook 正确封装分片上传逻辑

### Regression Evals
- [ ] 认证中间件正确拦截未授权请求
- [ ] RBAC 权限检查: viewer 角色无法创建/修改数据集
- [ ] 审计日志记录所有数据集 CRUD 操作
- [ ] 数据库迁移 (datasets 表含所有索引) 可重复执行
- [ ] S3 SSE-KMS 加密自动应用于所有上传对象
- [ ] S3 Bucket Policy 拒绝非 HTTPS 传输

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 后端单元测试覆盖率 >= 80%
- FR-006: 数据集上传速度 >= 100MB/s
- FR-007: 支持 >= 10TB 数据集
- FR-008: 版本控制支持 >= 100 个版本
- SC-005: S3 到 FSx 同步时间 <10 分钟 (1TB 数据集)
