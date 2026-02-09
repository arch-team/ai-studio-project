---
paths:
  - "stacks/**/*.py"
  - "config/environments.py"
---

# 成本优化规范

> **职责**: 定义资源选型、环境资源矩阵、存储优化、网络优化和成本监控策略。

> **职责边界**: 本文档关注**资源规格和成本控制**。环境配置的**代码架构**详见 [configuration.md](configuration.md)

---

## 0. 速查卡片

### 环境资源矩阵

| 资源 | Dev | Staging | Prod |
|------|-----|---------|------|
| NAT Gateway | 1 | 2 | 2 (每 AZ) |
| Aurora | db.t3.medium, 单 AZ | db.r6g.large, 多 AZ | db.r6g.xlarge, 多 AZ |
| EKS 系统节点 | t3.medium | t3.large | t3.xlarge |
| GPU 节点 | 1 x p4d.24xlarge | 2 x p4d.24xlarge | 4 x p5.48xlarge |
| FSx Lustre | 1.2 TiB | 2.4 TiB | 4.8+ TiB |

### GPU 实例成本参考

| 实例 | GPU | 按需价格 (us-west-2) | 月估算 (24x7) |
|------|-----|---------------------|--------------|
| p4d.24xlarge | 8x A100 | ~$32.77/h | ~$23,600/月 |
| p5.48xlarge | 8x H100 | ~$98.32/h | ~$70,800/月 |
| g5.xlarge | 1x A10G | ~$1.01/h | ~$727/月 |

### 必须标签

```python
# app.py - 应用到所有资源
required_tags = {
    "Project": "ai-training-platform",
    "Environment": env_config.environment_name,
    "CostCenter": "ai-platform",
    "ManagedBy": "cdk",
}
for key, value in required_tags.items():
    cdk.Tags.of(app).add(key, value)

# Prod 额外标签
if env_config.environment_name == "prod":
    cdk.Tags.of(app).add("Criticality", "high")
```

---

## 1. 计算优化

### GPU 节点管理

```python
# Kueue 队列控制 GPU 使用 (而非 Auto Scaling)
# GPU 节点成本高，通过 Kueue 队列管理任务调度

# Dev: 非训练时间不保留 GPU 节点
if env_config.environment_name == "dev":
    # 使用 Kueue 的 StopPolicy 暂停队列
    pass
```

### EKS 系统节点优化

```python
# 系统节点使用 Spot 实例 (非 GPU 节点)
if env_config.environment_name == "dev":
    capacity_type = eks.CapacityType.SPOT
else:
    capacity_type = eks.CapacityType.ON_DEMAND
```

---

## 2. 存储优化

### S3 生命周期 (必须)

```python
s3.Bucket(self, "TrainingDataBucket",
    lifecycle_rules=[
        s3.LifecycleRule(
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30)),
                s3.Transition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Duration.days(90)),
            ]),
        s3.LifecycleRule(
            noncurrent_version_expiration=Duration.days(30)),
        s3.LifecycleRule(
            abort_incomplete_multipart_upload_after=Duration.days(7)),
    ])
```

### FSx for Lustre 成本

| 部署类型 | 吞吐量 | 成本参考 (1.2 TiB) |
|---------|--------|-------------------|
| SCRATCH_2 | 200 MB/s/TiB | ~$140/月 |
| PERSISTENT_2 (250) | 250 MB/s/TiB | ~$350/月 |
| PERSISTENT_2 (1000) | 1000 MB/s/TiB | ~$700/月 |

```python
# Dev: SCRATCH_2 (低成本，数据非持久)
# Prod: PERSISTENT_2 (数据持久化)
deployment_type = (
    fsx.LustreDeploymentType.SCRATCH_2
    if env_config.environment_name == "dev"
    else fsx.LustreDeploymentType.PERSISTENT_2
)
```

### EBS: gp3 优于 gp2

```python
volume_type = ec2.EbsDeviceVolumeType.GP3  # 可自定义 IOPS/吞吐量，成本更低
```

---

## 3. 网络优化

### NAT Gateway 策略

| 环境 | NAT 配置 | 月成本参考 |
|------|---------|----------|
| Dev | 1 个 | ~$30/月 + 数据传输 |
| Staging/Prod | 每 AZ 一个 (2) | ~$60/月 + 数据传输 |

### VPC Endpoints (减少 NAT 流量)

```python
# Gateway Endpoints (免费) — 必须添加
vpc.add_gateway_endpoint("S3Endpoint",
    service=ec2.GatewayVpcEndpointAwsService.S3)

# Interface Endpoints (Prod 按需，~$7/月/端点)
if env_config.environment_name == "prod":
    for svc_name, svc in [
        ("ECR", ec2.InterfaceVpcEndpointAwsService.ECR),
        ("ECRDocker", ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER),
        ("STS", ec2.InterfaceVpcEndpointAwsService.STS),
    ]:
        vpc.add_interface_endpoint(svc_name, service=svc)
```

### EFA 网络成本

EFA (Elastic Fabric Adapter) 无额外费用，但需要特定实例类型 (p4d, p5) 和 Placement Group:

```python
# GPU 训练: 使用 Placement Group 确保低延迟
placement_group = ec2.PlacementGroup(self, "TrainingPG",
    strategy=ec2.PlacementGroupStrategy.CLUSTER)
```

---

## 4. 资源清理

### CloudWatch Logs 保留

```python
retention = (
    logs.RetentionDays.ONE_YEAR
    if env_config.environment_name == "prod"
    else logs.RetentionDays.ONE_WEEK
)
```

> RemovalPolicy 策略详见 [deployment.md §1](deployment.md)

---

## 5. 成本监控

### 预算告警

```python
budgets.CfnBudget(self, "MonthlyBudget",
    budget=budgets.CfnBudget.BudgetDataProperty(
        budget_limit=budgets.CfnBudget.SpendProperty(
            amount=5000 if env_config.environment_name == "prod" else 500,
            unit="USD"),
        budget_type="COST",
        time_unit="MONTHLY"),
    notifications_with_subscribers=[
        budgets.CfnBudget.NotificationWithSubscribersProperty(
            notification=budgets.CfnBudget.NotificationProperty(
                threshold=80,
                threshold_type="PERCENTAGE",
                comparison_operator="GREATER_THAN",
                notification_type="ACTUAL"),
            subscribers=[
                budgets.CfnBudget.SubscriberProperty(
                    address="platform-team@example.com",
                    subscription_type="EMAIL")])])
```

在 Billing Console 启用成本分配标签: `Project`, `Environment`, `CostCenter`

---

## 6. 审计清单

**月度**: 未使用 EBS 卷 | 未关联弹性 IP | 空闲 ALB | GPU 实例利用率 | S3 存储类

**季度**: Savings Plans 评估 | GPU 实例类型升级评估 (如 p4d → p5 性价比) | FSx 容量调整 | 跨区域数据传输

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [configuration.md](configuration.md) | 环境配置代码架构 |
| [hyperpod.md](hyperpod.md) | GPU 实例配置详情 |
| [deployment.md](deployment.md) | RemovalPolicy 策略 |
