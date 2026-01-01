# HyperPod Training Operator集成快速开始

## 前提条件

1. **Kubernetes集群**: AWS SageMaker HyperPod with EKS
2. **Training Operator**: HyperPod Training Operator已安装
3. **Kubeconfig**: 本地开发需要配置kubectl访问权限
4. **Python环境**: Python 3.11+

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增依赖:
- `jinja2==3.1.3` (模板引擎)

## 配置环境变量

创建或编辑 `backend/.env`:

```bash
# Kubernetes配置
K8S_NAMESPACE=ai-training-platform
K8S_CONFIG_PATH=~/.kube/config  # 本地开发时指定kubeconfig路径
K8S_IN_CLUSTER=false            # 生产环境设为true

# HyperPod配置
HYPERPOD_CLUSTER_NAME=my-hyperpod-cluster
HYPERPOD_TRAINING_OPERATOR_NAMESPACE=hyperpod-training-operator

# AWS配置(如需访问ECR镜像)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## 配置Kubernetes访问

### 本地开发(使用kubeconfig)

```bash
# 配置kubectl访问HyperPod集群
aws eks update-kubeconfig \
    --name <cluster-name> \
    --region us-west-2

# 验证连接
kubectl get nodes
kubectl get pytorchjobs -A
```

### 生产环境(in-cluster模式)

确保Pod的ServiceAccount具有以下权限:

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

## 测试集成

### 1. 启动后端服务

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 创建训练任务

使用API或前端界面创建训练任务:

```bash
curl -X POST "http://localhost:8000/api/v1/training/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-pytorch-training",
    "description": "测试HyperPod集成",
    "project_id": 1,
    "job_type": "DISTRIBUTED_DATA_PARALLEL",
    "framework": "PYTORCH",
    "config": {
      "node_count": 2,
      "gpu_per_node": 8,
      "docker_image": "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel",
      "command": ["python", "-m", "torch.distributed.launch"],
      "args": ["train.py", "--epochs", "100"],
      "env_vars": {"NCCL_DEBUG": "INFO"},
      "output_path": "/fsx/outputs/model-1"
    }
  }'
```

### 3. 启动训练任务

```bash
curl -X POST "http://localhost:8000/api/v1/training/jobs/{job_id}/start"
```

成功响应:
```json
{
  "id": 1,
  "name": "test-pytorch-training",
  "status": "QUEUED",
  "k8s_job_name": "test-pytorch-training-1-250101-120000",
  "k8s_namespace": "ai-training-project-1"
}
```

### 4. 验证K8s资源创建

```bash
# 查看PyTorchJob
kubectl get pytorchjobs -n ai-training-project-1

# 查看Job详情
kubectl describe pytorchjob test-pytorch-training-1-250101-120000 -n ai-training-project-1

# 查看Pods
kubectl get pods -l training-job-id=1 -n ai-training-project-1

# 查看Pod日志
kubectl logs <pod-name> -n ai-training-project-1
```

### 5. 同步任务状态

```bash
# 主动触发状态同步
curl -X POST "http://localhost:8000/api/v1/training/jobs/{job_id}/sync"

# 查看同步后的状态
curl "http://localhost:8000/api/v1/training/jobs/{job_id}"
```

## 验证检查清单

- [ ] 后端服务成功启动(无K8s连接错误)
- [ ] 创建训练任务成功(数据库记录创建)
- [ ] 启动任务后k8s_job_name字段被填充
- [ ] K8s中PyTorchJob资源创建成功
- [ ] PyTorchJob的Pod正常启动(非ImagePullBackOff/CrashLoopBackOff)
- [ ] 状态同步正常(QUEUED -> RUNNING -> COMPLETED)
- [ ] 停止任务后K8s资源被清理

## 常见问题排查

### 问题1: HyperPod Operator初始化失败

**症状:**
```
HyperPodOperatorError: K8s客户端初始化失败
```

**排查:**
1. 检查kubeconfig路径是否正确
2. 验证kubectl连接: `kubectl get nodes`
3. 检查ServiceAccount权限(生产环境)

### 问题2: PyTorchJob创建失败

**症状:**
```
JobCreationError: K8s API调用失败 (status=403): Forbidden
```

**排查:**
1. 检查RBAC权限(pytorchjobs资源是否有create权限)
2. 验证namespace存在: `kubectl get ns ai-training-project-1`
3. 检查Training Operator是否运行: `kubectl get pods -n hyperpod-training-operator`

### 问题3: Pod一直Pending

**症状:**
PyTorchJob创建成功但Pod不启动

**排查:**
1. 查看Pod事件: `kubectl describe pod <pod-name> -n ai-training-project-1`
2. 检查资源配额: GPU/CPU/内存是否充足
3. 验证节点标签: `kubectl get nodes --show-labels | grep instance-type`

### 问题4: 镜像拉取失败

**症状:**
```
ImagePullBackOff: Failed to pull image
```

**排查:**
1. 验证镜像存在: `docker pull pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel`
2. 检查ECR权限(如使用私有镜像)
3. 验证imagePullSecrets配置

## 下一步

1. **实现后台状态同步**: 使用Celery定期同步所有活跃任务状态
2. **添加API端点**:
   - `GET /jobs/{id}/status` - 查询K8s实时状态
   - `GET /jobs/{id}/logs` - 获取训练日志
   - `GET /jobs/{id}/pods` - 列出所有Pods
3. **集成监控**: Prometheus指标导出和Grafana仪表盘
4. **完善文档**: 添加更多使用示例和最佳实践

## 参考资料

- [T037实现总结](./T037-HyperPod-Operator-Implementation.md)
- [HyperPod Operator使用指南](../backend/src/services/training/operators/README.md)
- [AWS HyperPod文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator.html)
