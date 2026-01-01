# HyperPod Training Operator集成

## 概述

`HyperPodOperator` 负责与AWS SageMaker HyperPod Training Operator交互,管理Kubernetes `HyperPodPytorchJob` 自定义资源的完整生命周期。

## 核心功能

### 1. 创建训练任务 (create_pytorch_job)

基于Jinja2模板渲染Kubernetes PyTorchJob资源,并通过K8s API创建。

**特性:**
- 支持分布式训练(Master-Worker架构)
- 自动生成符合DNS-1123规范的Job名称
- 配置GPU资源、环境变量、存储卷
- 集成FSx for Lustre和本地NVMe存储

**错误处理:**
- `JobCreationError`: Job创建失败(K8s API错误、权限不足等)
- 自动回滚数据库状态

### 2. 查询任务状态 (get_job_status)

从Kubernetes查询PyTorchJob的实时状态。

**返回信息:**
- 任务状态(Pending/Running/Succeeded/Failed)
- 状态条件(Conditions)
- 副本状态(Master/Worker节点状态)
- 开始/完成时间

**错误处理:**
- `JobNotFoundError`: Job不存在(404)
- `JobStatusError`: 状态查询失败

### 3. 同步状态 (sync_job_status)

将Kubernetes状态同步到数据库,实现状态一致性。

**同步内容:**
- 任务状态映射(K8s -> TrainingJobStatus)
- 时间戳更新(started_at, completed_at)
- 错误信息提取(失败时自动获取Pod日志)

**状态映射:**
```python
K8s Status      -> TrainingJobStatus
Created         -> QUEUED
Running         -> RUNNING
Succeeded       -> COMPLETED
Failed          -> FAILED
```

### 4. 删除训练任务 (delete_job)

清理Kubernetes资源(PyTorchJob和关联的Pods)。

**特性:**
- 优雅删除(等待Pod终止)
- 幂等操作(已删除的Job不报错)

### 5. 获取Pod列表 (get_pod_list)

查询训练任务的所有Pod(用于日志查看、调试)。

## 使用示例

### 基础用法(通过TrainingJobService)

```python
from services.training.job_service import TrainingJobService

# 创建训练任务
async with get_session() as session:
    service = TrainingJobService(session)

    # 1. 创建任务记录
    job = await service.create_training_job(job_data, creator)

    # 2. 启动训练(自动创建K8s资源)
    job = await service.start_training_job(job.id)
    # K8s Job已创建: job.k8s_job_name

    # 3. 同步状态
    job = await service.sync_job_status(job.id)
    print(f"当前状态: {job.status.value}")

    # 4. 停止训练
    job = await service.stop_training_job(job.id)
    # K8s资源已清理
```

### 直接使用HyperPodOperator(高级)

```python
from services.training.operators import HyperPodOperator

# 初始化Operator
operator = HyperPodOperator(
    kubeconfig_path="~/.kube/config",  # 本地开发
    in_cluster=False,
)

# 创建PyTorchJob
k8s_job_name = await operator.create_pytorch_job(job, config)

# 查询状态
status_dict = await operator.get_job_status(
    job_name=k8s_job_name,
    namespace="ai-training-project-1",
)
print(f"K8s状态: {status_dict['status']}")
print(f"副本状态: {status_dict['replica_statuses']}")

# 获取Pod列表
pod_names = await operator.get_pod_list(
    job_name=k8s_job_name,
    namespace="ai-training-project-1",
)
print(f"训练Pods: {pod_names}")

# 删除Job
await operator.delete_job(
    job_name=k8s_job_name,
    namespace="ai-training-project-1",
)
```

## 配置要求

### 环境变量 (.env)

```bash
# Kubernetes配置
K8S_NAMESPACE=ai-training-platform
K8S_CONFIG_PATH=~/.kube/config  # 本地开发
K8S_IN_CLUSTER=false            # 生产环境设为true

# HyperPod配置
HYPERPOD_CLUSTER_NAME=my-hyperpod-cluster
HYPERPOD_TRAINING_OPERATOR_NAMESPACE=hyperpod-training-operator
```

### Kubernetes权限(RBAC)

Operator需要以下权限:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: training-platform-operator
rules:
  # PyTorchJob CRD操作
  - apiGroups: ["kubeflow.org"]
    resources: ["pytorchjobs"]
    verbs: ["create", "get", "list", "watch", "delete"]

  # Pod查询(日志、状态)
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list"]
```

### 依赖安装

```bash
pip install kubernetes==29.0.0 jinja2==3.1.3 pyyaml==6.0.1
```

## 模板配置

PyTorchJob模板位于: `backend/k8s/deployments/pytorch-job-template.yaml`

**支持的模板变量:**
- `job_name`: K8s Job名称
- `namespace`: K8s命名空间
- `job_id`: 数据库Job ID
- `node_count`: 训练节点数量
- `gpu_per_node`: 每节点GPU数
- `docker_image`: 训练容器镜像
- `command`, `args`: 训练命令和参数
- `env_vars`: 环境变量字典
- `dataset_path`, `output_path`: 数据和输出路径

**自定义模板:**

如需修改模板,编辑 `pytorch-job-template.yaml` 并确保:
1. 使用Jinja2语法(变量: `{{ var }}`, 条件: `{% if %} {% endif %}`)
2. 保留必需的label: `training-job-id: "{{ job_id }}"`
3. 资源限制正确配置(`nvidia.com/gpu`, `memory`, `cpu`)

## 错误处理最佳实践

### 1. Job创建失败

```python
try:
    job = await service.start_training_job(job_id)
except ValueError as e:
    # 数据库状态已回滚到FAILED
    # 检查错误信息: job.error_message
    if "quota exceeded" in str(e):
        # 资源配额不足
        pass
    elif "image not found" in str(e):
        # Docker镜像不存在
        pass
```

### 2. 状态同步失败

```python
try:
    job = await service.sync_job_status(job_id)
except ValueError as e:
    if "Job不存在" in str(e):
        # K8s Job已被外部删除,需要清理数据库记录
        pass
```

### 3. 网络或权限问题

```python
from services.training.operators import HyperPodOperatorError

try:
    operator = HyperPodOperator()
except HyperPodOperatorError as e:
    # K8s客户端初始化失败
    # 检查: kubeconfig路径、网络连接、ServiceAccount权限
    logger.error(f"Operator初始化失败: {e}")
```

## 监控和调试

### 查看K8s资源

```bash
# 列出所有PyTorchJob
kubectl get pytorchjobs -n ai-training-project-1

# 查看Job详情
kubectl describe pytorchjob <job-name> -n ai-training-project-1

# 查看Pod状态
kubectl get pods -l training-job-id=<job-id> -n ai-training-project-1

# 查看Pod日志
kubectl logs <pod-name> -n ai-training-project-1
```

### 使用HyperPod CLI

```bash
# 列出训练任务
hyp list hyp-pytorch-job

# 查看任务详情
hyp describe hyp-pytorch-job --job-name <job-name>

# 查看训练日志
hyp get-logs hyp-pytorch-job --pod-name <pod-name> --job-name <job-name>
```

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| Job创建后一直Pending | 资源配额不足 | 检查GPU配额、节点资源 |
| Pod ImagePullBackOff | 镜像不存在/权限不足 | 验证ECR镜像URL、IAM角色 |
| Training失败无日志 | 容器启动失败 | 检查command/args、环境变量 |
| 状态同步不及时 | 后台任务未启动 | 实现周期性状态同步任务 |

## 后续优化方向

1. **后台状态同步任务**: 使用Celery/APScheduler定期同步所有活跃任务状态
2. **Webhook集成**: 接收HyperPod Training Operator的状态变更事件
3. **多框架支持**: 添加TensorFlowJob、MXNetJob支持
4. **智能重试**: 实现指数退避重试策略(针对瞬时故障)
5. **资源预留**: 集成Kueue进行任务队列和资源调度
6. **成本优化**: 支持Spot实例、弹性训练(Elastic Training)

## 参考文档

- [AWS HyperPod Training Operator文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/)
- [PyTorchJob CRD规范](https://github.com/kubeflow/training-operator/blob/master/pkg/apis/kubeflow.org/v1/pytorch_types.go)
