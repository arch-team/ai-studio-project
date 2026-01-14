# AWS 集成测试

本目录包含针对真实 AWS 环境的集成测试，用于验证 S3 和 HyperPod 客户端的正确性。

## 前置条件

1. 配置 AWS 凭证
2. 创建测试用 S3 桶
3. (可选) 准备测试用 HyperPod 集群

## 配置

1. 复制配置模板：
   ```bash
   cp .env.aws-integration.example .env.aws-integration
   ```

2. 编辑 `.env.aws-integration` 填入你的配置

3. 加载环境变量：
   ```bash
   export $(cat .env.aws-integration | xargs)
   ```

## 运行测试

```bash
# 运行所有 AWS 集成测试
pytest -m aws_integration -v

# 仅运行 S3 测试
pytest -m aws_integration tests/integration/aws/test_s3_integration.py -v

# 仅运行 HyperPod 只读测试
pytest -m "aws_integration and hyperpod" tests/integration/aws/test_hyperpod_integration.py -v

# 跳过慢测试
pytest -m "aws_integration and not slow" -v
```

## 测试分类

### S3 测试 (test_s3_integration.py)

| 测试类 | 覆盖功能 |
|--------|---------|
| TestS3Upload | 文件上传、KMS 加密 |
| TestS3Download | 文件下载、内容完整性 |
| TestS3Delete | 文件删除、幂等性 |
| TestS3List | 列表查询、前缀过滤 |
| TestS3PresignedUrl | GET/PUT 预签名 URL |
| TestS3Copy | 文件复制 |
| TestS3Stream | 流式读取 |
| TestS3ErrorHandling | 错误处理 |

### HyperPod 测试 (test_hyperpod_integration.py)

| 测试类 | 覆盖功能 | 成本 |
|--------|---------|------|
| TestHyperPodReadOnly | list/describe 集群 | 免费 |
| TestHyperPodStatusMapping | 状态枚举验证 | 免费 |
| TestHyperPodErrorHandling | 错误处理 | 免费 |
| TestHyperPodWrite | 创建/删除集群 | **高** (默认禁用) |

## 成本控制

- S3 测试：每次运行约 $0.01 (取决于数据量)
- HyperPod 只读测试：免费
- HyperPod 写入测试：按实例计费 (**默认禁用**)

启用 HyperPod 写入测试：
```bash
export HYPERPOD_ENABLE_WRITE_TESTS=true
```

## 清理

测试自动清理创建的测试数据。如需手动清理：

```bash
# 清理 S3 测试数据
aws s3 rm s3://your-bucket/integration-tests/ --recursive

# 清理残留的测试集群 (如有)
aws sagemaker list-clusters --query "ClusterSummaries[?starts_with(ClusterName, 'integration-test')]"
```

## IAM 权限要求

测试账户需要以下最小权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3IntegrationTest",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket", "s3:HeadObject"],
      "Resource": ["arn:aws:s3:::your-test-bucket", "arn:aws:s3:::your-test-bucket/*"]
    },
    {
      "Sid": "HyperPodReadOnly",
      "Effect": "Allow",
      "Action": ["sagemaker:ListClusters", "sagemaker:DescribeCluster"],
      "Resource": "*"
    }
  ]
}
```
