---
paths:
  - "stacks/**/*.py"
  - "utils/nag_suppressions.py"
  - "utils/iam_helpers.py"
---

# CDK 安全规范

## 安全原则

1. **最小权限**: IAM 策略只授予必要权限
2. **深度防御**: 多层安全控制
3. **默认安全**: 安全配置为默认值
4. **加密一切**: 静态和传输数据加密

---

## IAM 最佳实践

### 角色设计

```python
def _create_training_role(self) -> iam.Role:
    """创建训练执行角色"""
    return iam.Role(
        self, "TrainingRole",
        assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        description="Role for training job execution",
        # ✅ 明确的会话时长
        max_session_duration=Duration.hours(12),
    )
```

### 策略编写

```python
# ✅ 正确: 精确的资源 ARN
policy = iam.PolicyStatement(
    actions=["s3:GetObject", "s3:PutObject"],
    resources=[
        f"arn:aws:s3:::{bucket_name}/training-data/*",
        f"arn:aws:s3:::{bucket_name}/checkpoints/*",
    ],
)

# ❌ 错误: 过于宽泛的权限
policy = iam.PolicyStatement(
    actions=["s3:*"],
    resources=["*"],
)
```

### 条件限制

```python
# ✅ 添加条件限制
policy = iam.PolicyStatement(
    actions=["s3:GetObject"],
    resources=[f"arn:aws:s3:::{bucket_name}/*"],
    conditions={
        "StringEquals": {
            "aws:PrincipalOrgID": "o-xxxxxxxxxx",
        },
    },
)
```

---

## 网络安全

### 安全组规则

```python
def _create_database_security_group(self, vpc: ec2.IVpc) -> ec2.SecurityGroup:
    """创建数据库安全组"""
    sg = ec2.SecurityGroup(
        self, "DatabaseSG",
        vpc=vpc,
        description="Security group for Aurora database",
        allow_all_outbound=False,  # ✅ 禁止默认出站
    )

    # ✅ 明确的入站规则
    sg.add_ingress_rule(
        peer=ec2.Peer.security_group_id(app_sg.security_group_id),
        connection=ec2.Port.tcp(3306),
        description="Allow MySQL from app layer",
    )

    return sg
```

### 子网隔离

```python
# 数据层使用隔离子网
self._db_cluster = rds.DatabaseCluster(
    self, "Database",
    vpc=vpc,
    vpc_subnets=ec2.SubnetSelection(
        subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,  # ✅ 隔离子网
    ),
)
```

---

## 数据加密

### S3 加密

```python
def _create_training_bucket(self) -> s3.Bucket:
    """创建训练数据桶"""
    return s3.Bucket(
        self, "TrainingBucket",
        encryption=s3.BucketEncryption.KMS,  # ✅ KMS 加密
        encryption_key=self._kms_key,
        bucket_key_enabled=True,  # ✅ 启用桶密钥降低成本
        enforce_ssl=True,  # ✅ 强制 HTTPS
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # ✅ 阻止公开访问
        versioned=True,  # ✅ 启用版本控制
    )
```

### 数据库加密

```python
self._cluster = rds.DatabaseCluster(
    self, "Database",
    storage_encrypted=True,  # ✅ 存储加密
    storage_encryption_key=self._kms_key,
)
```

### EBS 加密

```python
launch_template = ec2.LaunchTemplate(
    self, "LaunchTemplate",
    block_devices=[
        ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=200,
                encrypted=True,  # ✅ EBS 加密
                encryption_key=self._kms_key,
            ),
        ),
    ],
)
```

---

## KMS 密钥管理

### 密钥创建

```python
def _create_kms_key(self) -> kms.Key:
    """创建 KMS 密钥"""
    return kms.Key(
        self, "DataKey",
        description="Key for encrypting training data",
        enable_key_rotation=True,  # ✅ 自动轮换
        alias=f"alias/{self._env_config.project_name}-data-key",
        removal_policy=(
            RemovalPolicy.RETAIN
            if self._env_config.protection.deletion_protection
            else RemovalPolicy.DESTROY
        ),
        pending_window=Duration.days(30),  # ✅ 待删除窗口
    )
```

### 密钥策略

```python
# 限制密钥使用者
key.add_to_resource_policy(
    iam.PolicyStatement(
        principals=[iam.ServicePrincipal("sagemaker.amazonaws.com")],
        actions=["kms:Decrypt", "kms:GenerateDataKey"],
        resources=["*"],
        conditions={
            "StringEquals": {
                "kms:ViaService": f"sagemaker.{self.region}.amazonaws.com",
            },
        },
    )
)
```

---

## EC2 实例安全

### IMDSv2 强制

```python
launch_template = ec2.LaunchTemplate(
    self, "LaunchTemplate",
    require_imdsv2=True,  # ✅ 强制 IMDSv2
)
```

### 无 SSH 访问

```python
# EKS 节点组不允许 SSH
nodegroup = eks.Nodegroup(
    self, "NodeGroup",
    remote_access=None,  # ✅ 禁用 SSH
)
```

---

## ALB 安全

### TLS 配置

```python
def _create_alb(self) -> elbv2.ApplicationLoadBalancer:
    """创建 ALB"""
    alb = elbv2.ApplicationLoadBalancer(
        self, "ALB",
        vpc=self._vpc,
        internet_facing=True,
        drop_invalid_header_fields=True,  # ✅ 丢弃无效头
    )

    # ✅ HTTPS 监听器
    listener = alb.add_listener(
        "HttpsListener",
        port=443,
        certificates=[self._certificate],
        ssl_policy=elbv2.SslPolicy.TLS12,  # ✅ TLS 1.2+
    )

    # ✅ HTTP 重定向到 HTTPS
    alb.add_redirect(source_port=80, target_port=443)

    return alb
```

### WAF 集成

```python
def _create_waf(self) -> wafv2.CfnWebACL:
    """创建 WAF (仅生产环境)"""
    if not self._env_config.protection.waf_enabled:
        return None

    return wafv2.CfnWebACL(
        self, "WebACL",
        default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
        scope="REGIONAL",
        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
            cloud_watch_metrics_enabled=True,
            metric_name="WebACLMetric",
            sampled_requests_enabled=True,
        ),
        rules=[
            # AWS 托管规则
            self._create_aws_managed_rule("AWSManagedRulesCommonRuleSet", 1),
            self._create_aws_managed_rule("AWSManagedRulesKnownBadInputsRuleSet", 2),
            self._create_aws_managed_rule("AWSManagedRulesSQLiRuleSet", 3),
        ],
    )
```

---

## 日志和审计

### VPC Flow Logs

```python
def _enable_flow_logs(self, vpc: ec2.Vpc) -> None:
    """启用 VPC Flow Logs"""
    vpc.add_flow_log(
        "FlowLog",
        destination=ec2.FlowLogDestination.to_cloud_watch_logs(
            log_group=logs.LogGroup(
                self, "FlowLogGroup",
                retention=logs.RetentionDays.ONE_MONTH,
            ),
        ),
        traffic_type=ec2.FlowLogTrafficType.ALL,
    )
```

### S3 访问日志

```python
# 访问日志桶
access_logs_bucket = s3.Bucket(
    self, "AccessLogsBucket",
    encryption=s3.BucketEncryption.S3_MANAGED,
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    lifecycle_rules=[
        s3.LifecycleRule(
            expiration=Duration.days(90),
        ),
    ],
)

# 启用访问日志
training_bucket = s3.Bucket(
    self, "TrainingBucket",
    server_access_logs_bucket=access_logs_bucket,
    server_access_logs_prefix="training-bucket/",
)
```

---

## CDK Nag 集成

### 配置

```python
# app.py
from cdk_nag import AwsSolutionsChecks, NagSuppressions

app = cdk.App()

# 创建 Stacks...

# 应用安全检查 (staging/prod)
if not env_config.protection.skip_cdk_nag:
    cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
```

### 抑制规则管理

```python
# utils/nag_suppressions.py
"""CDK Nag 抑制规则"""

COMMON_SUPPRESSIONS = [
    {
        "id": "AwsSolutions-IAM4",
        "reason": "AWS managed policies used for EKS node roles",
    },
]

STACK_SPECIFIC_SUPPRESSIONS = {
    "network": [
        {
            "id": "AwsSolutions-VPC7",
            "reason": "VPC Flow Logs enabled at VPC level",
        },
    ],
    "database": [
        {
            "id": "AwsSolutions-RDS10",
            "reason": "Deletion protection controlled by environment config",
        },
    ],
}

def apply_nag_suppressions(app: cdk.App) -> None:
    """应用所有 CDK Nag 抑制规则"""
    # 应用通用规则
    NagSuppressions.add_stack_suppressions(
        app,
        COMMON_SUPPRESSIONS,
    )

    # 应用 Stack 特定规则
    for stack_id, suppressions in STACK_SPECIFIC_SUPPRESSIONS.items():
        stack = app.node.try_find_child(stack_id)
        if stack:
            NagSuppressions.add_stack_suppressions(stack, suppressions)
```

---

## 资源保护

### 删除保护

```python
# 数据库删除保护
self._cluster = rds.DatabaseCluster(
    self, "Database",
    deletion_protection=self._env_config.protection.deletion_protection,
    removal_policy=(
        RemovalPolicy.RETAIN
        if self._env_config.protection.deletion_protection
        else RemovalPolicy.DESTROY
    ),
)

# S3 桶保护
bucket = s3.Bucket(
    self, "DataBucket",
    removal_policy=(
        RemovalPolicy.RETAIN
        if self._env_config.protection.deletion_protection
        else RemovalPolicy.DESTROY
    ),
    auto_delete_objects=not self._env_config.protection.deletion_protection,
)
```

### 备份策略

```python
# Aurora 备份
self._cluster = rds.DatabaseCluster(
    self, "Database",
    backup=rds.BackupProps(
        retention=Duration.days(self._env_config.database.backup_retention_days),
        preferred_window="02:00-03:00",  # UTC
    ),
)
```

---

## 安全检查清单

### 部署前检查

- [ ] IAM 策略遵循最小权限原则
- [ ] 所有数据存储启用加密
- [ ] KMS 密钥启用自动轮换
- [ ] VPC Flow Logs 已启用
- [ ] 安全组规则明确且最小化
- [ ] ALB 使用 TLS 1.2+
- [ ] 生产环境 WAF 已启用
- [ ] CDK Nag 检查通过 (staging/prod)

### 环境特定要求

| 检查项 | Dev | Staging | Prod |
|--------|-----|---------|------|
| CDK Nag | 跳过 | 必须 | 必须 |
| WAF | 可选 | 推荐 | 必须 |
| 删除保护 | 关闭 | 开启 | 开启 |
| 多 AZ | 可选 | 必须 | 必须 |
| 备份保留 | 7天 | 7天 | 14天 |
