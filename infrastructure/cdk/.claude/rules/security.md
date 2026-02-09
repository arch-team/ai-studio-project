---
paths:
  - "stacks/**/*.py"
  - "utils/nag_suppressions.py"
  - "utils/iam_helpers.py"
---

# 安全规范

## 核心原则

1. **最小权限**: IAM 只授予必要权限
2. **加密一切**: 静态和传输数据加密
3. **默认安全**: 安全配置为默认值

## IAM 策略

```python
# ✅ 精确资源
iam.PolicyStatement(
    actions=["s3:GetObject", "s3:PutObject"],
    resources=[f"arn:aws:s3:::{bucket}/training-data/*"],
)

# ❌ 禁止
actions=["s3:*"], resources=["*"]
```

## 网络安全

```python
# 安全组: 禁止默认出站
sg = ec2.SecurityGroup(self, "SG", vpc=vpc, allow_all_outbound=False)

# 数据层: 隔离子网
vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
```

## 加密配置

| 资源 | 配置 |
|------|------|
| S3 | `encryption=KMS`, `enforce_ssl=True`, `block_public_access=BLOCK_ALL` |
| RDS | `storage_encrypted=True` |
| EBS | `encrypted=True` |
| KMS | `enable_key_rotation=True` |

```python
s3.Bucket(self, "Bucket",
    encryption=s3.BucketEncryption.KMS,
    enforce_ssl=True,
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL)
```

## EC2 安全

```python
ec2.LaunchTemplate(self, "LT", require_imdsv2=True)  # 强制 IMDSv2
eks.Nodegroup(self, "NG", remote_access=None)        # 禁用 SSH
```

## ALB 安全

```python
alb.add_listener("Https", port=443, ssl_policy=elbv2.SslPolicy.TLS12)
alb.add_redirect(source_port=80, target_port=443)  # HTTP→HTTPS
```

## CDK Nag

```python
# app.py - 所有环境无条件启用
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
apply_nag_suppressions(app)  # 集中管理已知误报的 suppression
```

## 环境安全要求

> 完整的环境差异矩阵见 [configuration.md](configuration.md)

**安全相关要点**: CDK Nag 所有环境无条件启用 | WAF prod 必须 | 删除保护 staging/prod 启用
