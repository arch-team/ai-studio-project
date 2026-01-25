# 修复 AWS Region 配置不一致

## 问题摘要

项目默认 AWS region 为 `us-east-1`，但发现两处配置使用了 `us-west-2`。

## 修改清单

### 1. S3StorageClient 默认 region

**文件**: `backend/src/shared/infrastructure/storage/s3_client.py`
**行号**: 24
**修改**: `region: str = "us-west-2"` → `region: str = "us-east-1"`

### 2. 集成测试环境配置

**文件**: `backend/.env.aws-integration.example`
**行号**: 14
**修改**: `AWS_REGION=us-west-2` → `AWS_REGION=us-east-1`

## 验证方式

```bash
# 确认所有 region 配置一致
grep -r "us-west-2" backend/src/ backend/.env*
# 预期结果：无匹配
```
