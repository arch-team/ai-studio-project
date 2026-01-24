# 实施计划: SC-001 和 SC-002 真实 AWS E2E 测试验证

## 任务概述

在真实 AWS HyperPod 环境执行 E2E 测试，验证：
- **SC-001**: 支持 PyTorch DDP/FSDP/DeepSpeed ZeRO
- **SC-002**: 检查点保存成功率 >99%

## 当前状态分析

| 测试类型 | 文件 | 环境 | 状态 |
|---------|------|------|------|
| 集成测试 | `test_preemption_timing.py` | Mock 模拟 | ✅ 逻辑已验证 |
| E2E 测试 | `test_e2e_preemption_sla.py` | 真实 AWS | ⏳ 待执行 |

## 执行计划

### 阶段 1: 环境准备

**必需环境变量配置:**

```bash
# AWS 凭证 (支持 SSO/配置文件/环境变量)
export AWS_REGION=us-west-2

# HyperPod 集群配置
export HYPERPOD_CLUSTER_NAME=<your-cluster-name>

# 启用写入测试 (创建真实任务)
export E2E_READ_ONLY=false

# 测试账号配置
export E2E_ADMIN_USERNAME=admin
export E2E_ADMIN_PASSWORD=<password>

# 可选: 自定义测试镜像和实例类型
export TEST_IMAGE_URI=763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:2.1.0-gpu-py310-cu121-ubuntu20.04-sagemaker
export TEST_INSTANCE_TYPE=ml.g5.xlarge
export TEST_CHECKPOINT_S3_PATH=s3://ai-training-checkpoints-dev/e2e-tests/
```

**前提条件检查:**
1. AWS 凭证已配置 (`aws sts get-caller-identity` 成功)
2. HyperPod 集群已创建并运行
3. Kueue 调度器已配置优先级队列
4. S3 检查点存储桶已创建
5. 测试账号具有必要权限

### 阶段 2: 执行 E2E 测试

**运行命令:**

```bash
cd backend

# 运行全部抢占 SLA E2E 测试
pytest tests/e2e/aws/test_e2e_preemption_sla.py -v -s

# 运行单个测试场景 (调试用)
pytest tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_checkpoint_saved_within_sla -v -s
```

**测试场景清单:**

| 场景 | 测试方法 | SLA 要求 | 验证目标 |
|------|---------|---------|---------|
| 1 | `test_low_priority_preempted_by_high_priority` | - | SC-001: 抢占机制 |
| 2 | `test_checkpoint_saved_within_sla` | ≤5 分钟 | SC-002: 检查点保存 |
| 3 | `test_pod_released_within_sla` | ≤30 秒 | Pod 释放时序 |
| 4 | `test_job_status_transition_to_preempted` | - | 状态转换正确性 |
| 5 | `test_auto_recovery_from_preemption` | - | 自动恢复机制 |

### 阶段 3: 结果验证

**预期输出:**

```
tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_low_priority_preempted_by_high_priority PASSED
tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_checkpoint_saved_within_sla PASSED
tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_pod_released_within_sla PASSED
tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_job_status_transition_to_preempted PASSED
tests/e2e/aws/test_e2e_preemption_sla.py::TestPreemptionTimingSLAE2E::test_auto_recovery_from_preemption PASSED
```

**SLA 验证关键指标:**

| 指标 | 阈值 | 来源 |
|------|------|------|
| Checkpoint 保存时间 | < 300 秒 | `SLAConstants.CHECKPOINT_SAVE_TIMEOUT` |
| Pod 释放时间 | < 30 秒 | `SLAConstants.POD_RELEASE_TIMEOUT` |
| 最大抢占次数 | 3 次 | `SLAConstants.MAX_PREEMPTION_COUNT` |

### 阶段 4: 更新任务状态

测试通过后，确认 `tasks.md` 中以下任务标记为完成:
- [X] T038c - 抢占时序 SLA 集成测试 (真实 AWS 验证)

## 关键文件

| 文件 | 用途 |
|------|------|
| `backend/tests/e2e/aws/test_e2e_preemption_sla.py` | E2E 测试主文件 (785 行) |
| `backend/tests/e2e/aws/conftest.py` | AWS 配置和 Fixture (338 行) |
| `backend/tests/integration/training/test_preemption_timing.py` | Mock 集成测试 (712 行) |

## 风险和注意事项

⚠️ **成本提醒**: E2E 测试会创建真实 GPU 训练任务，注意成本控制

⚠️ **资源清理**: 测试完成后确保所有资源被清理 (测试代码的 `finally` 块会处理)

⚠️ **权限要求**: 测试账号需要 SageMaker、EKS、S3 相关权限

---

**计划创建时间**: 2026-01-24
**执行前提**: HyperPod 集群可用、Kueue 已配置
