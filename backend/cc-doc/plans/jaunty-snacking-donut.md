# 计划：HyperPod E2E 抢占测试执行

## 目标

在真实 HyperPod 集群上验证训练任务抢占流程，完成 eval 中的 E2E 验证项。

## 前提条件

### 必需资源
- AWS 账号和凭证（`aws configure` 已配置）
- HyperPod 集群（已启用 Task Governance）
- Kueue 配置（PriorityClass、LocalQueue、ClusterQueue）
- S3 存储桶（用于 Checkpoint）

### 集群配置要求
```
Task Governance 需要：
├── hyperpod-ns-e2e-low/         # 低优先级 namespace
│   └── low-localqueue           # LocalQueue
├── hyperpod-ns-e2e-high/        # 高优先级 namespace
│   └── high-localqueue          # LocalQueue
└── PriorityClass
    ├── low-priority (100)
    └── high-priority (1000)
```

## 执行步骤

### 步骤 1：配置环境变量

创建 `.env.e2e.dev` 文件：

```bash
cd backend
cp .env.e2e.example .env.e2e.dev
```

编辑必填字段：

| 变量 | 示例值 | 说明 |
|------|--------|------|
| `AWS_REGION` | `us-west-2` | HyperPod 集群区域 |
| `AWS_ACCOUNT_ID` | `123456789012` | AWS 账号 ID |
| `HYPERPOD_CLUSTER_NAME` | `my-hyperpod-cluster` | 集群名称 |
| `E2E_READ_ONLY` | `false` | **必须设为 false** |
| `E2E_LOW_NAMESPACE` | `hyperpod-ns-e2e-low` | 低优先级 namespace |
| `E2E_HIGH_NAMESPACE` | `hyperpod-ns-e2e-high` | 高优先级 namespace |
| `CHECKPOINT_S3_BUCKET` | `my-checkpoint-bucket` | S3 桶名称 |

### 步骤 2：验证集群连接

```bash
# 验证 AWS 凭证
aws sts get-caller-identity

# 验证 HyperPod 集群
aws sagemaker describe-cluster --cluster-name $HYPERPOD_CLUSTER_NAME

# 验证 kubectl 连接
kubectl get nodes
kubectl get workloadpriorityclasses  # Kueue PriorityClass
kubectl get localqueues -A           # LocalQueue
```

### 步骤 3：运行 E2E 抢占测试

```bash
cd backend
source .venv/bin/activate

# 加载环境变量
set -a && source .env.e2e.dev && set +a

# 运行抢占 SLA 测试（5 个场景）
pytest tests/e2e/aws/test_e2e_preemption_sla.py -v -s

# 或只运行特定测试
pytest tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionSLA::test_low_priority_preempted_by_high_priority -v -s
```

### 步骤 4：验证测试场景

| 场景 | 测试名称 | 预期结果 |
|------|---------|---------|
| 1 | `test_low_priority_preempted_by_high_priority` | 低优先级任务被高优先级抢占 |
| 2 | `test_checkpoint_saved_within_sla` | Checkpoint 在 5 分钟内保存到 S3 |
| 3 | `test_pod_released_within_sla` | Pod 在 30 秒内释放 |
| 4 | `test_job_status_transition_to_preempted` | 状态正确转换为 PREEMPTED |
| 5 | `test_auto_recovery_from_preemption` | 从 Checkpoint 自动恢复成功 |

## 关键文件

| 文件 | 用途 |
|------|------|
| `backend/.env.e2e.example` | 环境变量模板 |
| `backend/tests/e2e/config/settings.py` | 配置管理 |
| `backend/tests/e2e/aws/conftest.py` | AWS Fixture |
| `backend/tests/e2e/aws/test_e2e_preemption_sla.py` | 抢占测试场景 |

## 验证完成

测试通过后，更新 eval 文件：

```markdown
# .claude/evals/hyperpod-training-job-preemption.md

E2E HyperPod: PASSED
- test_low_priority_preempted_by_high_priority: PASS
- test_checkpoint_saved_within_sla: PASS
- test_pod_released_within_sla: PASS
- test_job_status_transition_to_preempted: PASS
- test_auto_recovery_from_preemption: PASS
```

## 故障排除

### 常见问题

1. **Skip: HyperPod cluster not configured**
   - 检查 `HYPERPOD_CLUSTER_NAME` 是否设置

2. **Skip: E2E_READ_ONLY is true**
   - 设置 `E2E_READ_ONLY=false`

3. **Job status always None**
   - 确保 `set_cluster_context()` 已调用
   - 检查 kubeconfig 是否正确

4. **Checkpoint not found in S3**
   - 检查训练脚本是否包含 checkpoint 保存逻辑
   - 验证 S3 桶权限

5. **Kueue LocalQueue not found**
   - 验证 namespace 和 queue 名称匹配
   - 检查 ClusterQueue 配额是否足够
