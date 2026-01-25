## EVAL: T047 - S3 上传集成

Created: 2025-01-25
Task: `backend/src/modules/datasets/application/services/dataset_upload_service.py`
Requirements: FR-006 (≥100MB/s 上传速度), FR-007 (≥10TB 数据集支持)

---

### 能力评估 (Capability Evals) - 使用真实 AWS 环境

#### 基础功能

- [ ] **C1.1 分片上传初始化**: 调用 `initiate_multipart_upload()` 成功返回 `upload_id`，S3 CreateMultipartUpload API 调用成功
  - 验证命令: `aws s3api list-multipart-uploads --bucket ${BUCKET_NAME} | jq '.Uploads | length'`
  - 通过条件: 返回的 upload_id 格式正确，S3 控制台可见未完成的分片上传

- [ ] **C1.2 预签名 URL 生成**: `generate_presigned_urls()` 生成的 URL 可用于分片上传
  - 验证方法: 使用 `curl -X PUT --upload-file part.bin "${PRESIGNED_URL}"` 上传分片
  - 通过条件: HTTP 200，返回 ETag 头

- [ ] **C1.3 分片完成注册**: `register_part_completion()` 正确记录分片信息到数据库
  - 验证命令: `SELECT * FROM upload_sessions WHERE upload_id = '${UPLOAD_ID}'`
  - 通过条件: `completed_parts` JSON 包含注册的分片信息

- [ ] **C1.4 上传进度查询**: `get_upload_progress()` 返回准确的上传进度
  - 通过条件: `progress_percentage` = (已上传字节 / 总字节) × 100，精确到小数点后两位

- [ ] **C1.5 完成分片上传**: `complete_multipart_upload()` 成功合并所有分片
  - 验证命令: `aws s3api head-object --bucket ${BUCKET_NAME} --key ${KEY}`
  - 通过条件: 对象存在，ContentLength 等于原始文件大小

- [ ] **C1.6 取消分片上传**: `abort_multipart_upload()` 成功清理未完成上传
  - 验证命令: `aws s3api list-multipart-uploads --bucket ${BUCKET_NAME} --prefix ${PREFIX}`
  - 通过条件: 取消后无残留的分片上传

#### 断点续传

- [ ] **C2.1 会话持久化**: 上传会话正确保存到数据库，支持跨会话恢复
  - 测试流程: 上传部分分片 → 中断 → 重启服务 → 查询会话 → 继续上传
  - 通过条件: 会话信息完整，可继续未完成的上传

- [ ] **C2.2 分片重试**: 单个分片失败后可重新上传，不影响其他分片
  - 测试方法: 注册同一 part_number 两次，验证最新 ETag 被记录
  - 通过条件: 数据库记录最新的分片信息

- [ ] **C2.3 活跃会话检测**: 同一数据集不允许重复创建活跃上传会话
  - 通过条件: 第二次 `initiate_multipart_upload()` 抛出 `UploadSessionActiveError`

#### MD5 校验和

- [ ] **C3.1 分片校验和记录**: 每个分片的 MD5 校验和正确存储
  - 通过条件: `completed_parts[n].md5_checksum` 与客户端计算值一致

- [ ] **C3.2 完整性验证**: 完成上传时可验证所有分片校验和
  - 通过条件: S3 ETag 格式为 `{hash}-{part_count}`，与预期一致

#### 性能要求 (FR-006)

- [ ] **C4.1 分片大小配置**: 默认分片大小为 100MB
  - 验证: `DEFAULT_PART_SIZE == 100 * 1024 * 1024`

- [ ] **C4.2 大文件支持 (FR-007)**: 支持 ≥10TB 文件 (10000 × 100MB × 10)
  - 验证: `MAX_PARTS == 10000`，理论最大支持 1PB

- [ ] **C4.3 上传速度基准**: 单线程上传速度 ≥100MB/s (取决于网络和 S3 区域)
  - 测试命令: 上传 1GB 文件，测量耗时
  - 通过条件: 在 AWS 网络内 (EC2/HyperPod) 耗时 <10秒

#### 错误处理

- [ ] **C5.1 数据集不存在**: `initiate_multipart_upload()` 对不存在的 dataset_id 抛出 `DatasetNotFoundError`
- [ ] **C5.2 会话不存在**: 对无效 upload_id 抛出 `UploadSessionNotFoundError`
- [ ] **C5.3 上传未完成**: 缺少分片时 `complete_multipart_upload()` 抛出 `UploadIncompleteError`

---

### 回归评估 (Regression Evals)

- [ ] **R1 现有单元测试通过**: `pytest tests/unit/modules/datasets/ -v` 全部通过
- [ ] **R2 S3 客户端封装**: `S3MultipartClient` 所有方法正常工作
- [ ] **R3 上传会话仓库**: `UploadSessionRepository` CRUD 操作正常
- [ ] **R4 数据集状态更新**: 上传完成后数据集状态从 PREPARING → AVAILABLE

---

### 集成测试场景 (真实 AWS 环境)

#### 端到端测试

```bash
# 环境变量
export AWS_REGION=us-west-2
export S3_BUCKET_NAME=ai-training-platform-datasets-dev
export TEST_DATASET_ID=1

# 测试脚本位置
# tests/integration/datasets/test_s3_upload_integration.py
pytest tests/integration/datasets/test_s3_upload_integration.py -v
```

#### 测试场景列表

| 场景 | 描述 | 验证方法 |
|------|------|----------|
| **E2E-1** | 小文件上传 (50MB) | 单分片上传，验证完整性 |
| **E2E-2** | 标准文件上传 (500MB) | 5 分片上传，验证 ETag |
| **E2E-3** | 大文件上传 (2GB) | 20 分片上传，验证进度 |
| **E2E-4** | 断点续传模拟 | 上传 5/10 分片 → 恢复 → 完成 |
| **E2E-5** | 并发分片上传 | 同时上传多个分片，验证顺序无关性 |
| **E2E-6** | 取消上传清理 | 上传部分 → 取消 → 验证 S3 清理 |

---

### 成功标准

- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- FR-006: 上传速度 ≥100MB/s (AWS 网络内)
- FR-007: 支持 ≥10TB 文件 (验证分片配置)

---

### AWS 资源要求

| 资源 | 要求 | 用途 |
|------|------|------|
| **S3 Bucket** | SSE-KMS 加密，版本控制 | 存储测试数据集 |
| **IAM Role** | s3:PutObject, s3:GetObject, s3:AbortMultipartUpload | API 调用权限 |
| **VPC Endpoint** | S3 Gateway Endpoint | 避免公网流量 |
| **测试数据** | 50MB, 500MB, 2GB 测试文件 | 端到端测试 |

---

### 手动验证检查清单

- [ ] S3 Bucket 存在且配置正确
- [ ] 分片上传在 S3 控制台可见 (进行中)
- [ ] 完成上传后对象可下载验证
- [ ] 取消上传后无残留分片
- [ ] CloudWatch 日志记录上传事件
