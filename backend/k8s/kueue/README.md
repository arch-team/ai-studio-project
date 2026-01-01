# Kueue Gang Scheduling配置指南

本目录包含AWS SageMaker HyperPod集群的Kueue Gang Scheduling配置资源。

## 什么是Gang Scheduling

Gang Scheduling(组调度)确保分布式训练任务的所有Pod同时被调度,避免部分Pod等待导致的资源浪费。对于多节点训练任务(如8节点GPU训练),Kueue保证要么全部8个Pod同时启动,要么都不启动,直到资源满足。

## Kueue在HyperPod中的作用

AWS HyperPod Task Governance使用Kueue v0.12.0进行:
- **资源配额管理**: 通过ClusterQueue和LocalQueue管理GPU/CPU/Memory配额
- **优先级调度**: 使用WorkloadPriorityClass定义任务优先级(low/normal/high)
- **公平调度**: 支持多团队资源借用(quota lending/borrowing)
- **拓扑感知**: 优化大规模训练的网络拓扑(可选)

## 配置层次结构

```
ClusterQueue (集群级别资源池)
    ↓ 引用
ResourceFlavor (GPU/CPU资源类型定义)
    ↓ 关联
LocalQueue (项目/团队级别队列)
    ↓ 引用
PyTorchJob (训练任务)
    ↓ 使用
WorkloadPriorityClass (优先级定义)
```

## 快速开始

### 1. 安装Kueue CRD(HyperPod已预装)

HyperPod集群已预装Kueue v0.12.0,无需手动安装。验证安装:

```bash
kubectl get crd | grep kueue
# 输出: clusterqueues.kueue.x-k8s.io, localqueues.kueue.x-k8s.io, etc.
```

### 2. 创建ClusterQueue和ResourceFlavor

```bash
kubectl apply -f cluster-queue.yaml
kubectl apply -f resource-flavor.yaml
```

### 3. 为每个项目创建LocalQueue

```bash
# 编辑local-queue-template.yaml,替换{PROJECT_ID}
kubectl apply -f local-queue-project-1.yaml
```

### 4. 创建优先级类别

```bash
kubectl apply -f workload-priority-classes.yaml
```

### 5. 验证配置

```bash
# 查看ClusterQueue状态
kubectl get clusterqueue ml-gpu-cluster-queue -o yaml

# 查看LocalQueue
kubectl get localqueue -n ai-training-1

# 查看WorkloadPriorityClass
kubectl get workloadpriorityclass
```

## 使用示例

### 在训练任务中指定优先级和队列

通过AI训练平台API创建任务时:

```json
{
  "name": "bert-pretraining",
  "priority": "high",
  "queue_name": "project-1-queue",
  "config": {
    "node_count": 8,
    "gpu_per_node": 8,
    ...
  }
}
```

平台自动生成PyTorchJob manifest:

```yaml
metadata:
  annotations:
    kueue.x-k8s.io/queue-name: "project-1-queue"
  labels:
    kueue.x-k8s.io/priority-class: "high"
spec:
  runPolicy:
    suspend: true  # 初始suspended,等待Kueue调度
```

### 监控调度状态

```bash
# 查看Workload(Kueue的任务抽象)
kubectl get workloads -n ai-training-1

# 查看Workload详情
kubectl describe workload <workload-name> -n ai-training-1

# 查看ClusterQueue使用情况
kubectl get clusterqueue ml-gpu-cluster-queue -o jsonpath='{.status}'
```

## 配置调优

### 优先级权重建议

- **low** (100): 实验性训练,可被抢占
- **normal** (1000): 常规训练任务
- **high** (10000): 生产模型训练,紧急任务

### 资源配额策略

**保守策略**(资源稀缺):
- ClusterQueue: 总资源80%
- LocalQueue: 平均分配 + 10%借用上限

**激进策略**(资源充足):
- ClusterQueue: 总资源100%
- LocalQueue: 平均分配 + 30%借用上限

### 拓扑感知调度(大规模训练)

对于>32节点的训练任务,启用拓扑感知:

```yaml
metadata:
  annotations:
    kueue.x-k8s.io/podset-required-topology: "topology.k8s.aws/network-node-layer-2"
```

这确保所有Pod调度到同一网络拓扑层,降低通信延迟。

## 故障排查

### 任务卡在Pending

**症状**: PyTorchJob状态为suspended=true,长时间未启动

**原因1**: 资源配额不足
```bash
kubectl describe clusterqueue ml-gpu-cluster-queue
# 查看usedResources vs nominalQuota
```

**解决**: 等待资源释放或增加配额

**原因2**: 优先级被更高优先级任务抢占
```bash
kubectl get workloads -n ai-training-1 --sort-by=.spec.priority
```

**解决**: 提高任务优先级或等待高优先级任务完成

### 任务未加入队列

**症状**: PyTorchJob创建成功,但没有对应Workload

**原因**: queue_name或priority-class不存在

```bash
kubectl get localqueue <queue-name> -n <namespace>
kubectl get workloadpriorityclass <priority-class>
```

**解决**: 确保LocalQueue和WorkloadPriorityClass已创建

### ClusterQueue配额耗尽

**症状**: 所有队列的任务都pending

```bash
kubectl get clusterqueue ml-gpu-cluster-queue -o jsonpath='{.status.flavorsUsage}'
```

**解决**:
1. 停止不必要的训练任务释放资源
2. 联系管理员增加ClusterQueue配额

## 高级功能

### 多ResourceFlavor(异构GPU)

支持不同GPU型号(如P4d vs P5实例):

```yaml
# resource-flavor-p4d.yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: gpu-p4d
spec:
  nodeLabels:
    node.kubernetes.io/instance-type: p4d.24xlarge

# resource-flavor-p5.yaml (更高性能)
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: gpu-p5
spec:
  nodeLabels:
    node.kubernetes.io/instance-type: p5.48xlarge
```

在ClusterQueue中配置flavor选择:

```yaml
spec:
  resourceGroups:
  - flavors:
    - name: gpu-p5
      resources:
      - name: nvidia.com/gpu
        nominalQuota: 128
    - name: gpu-p4d  # fallback flavor
      resources:
      - name: nvidia.com/gpu
        nominalQuota: 256
```

### 配额借用(Quota Lending/Borrowing)

允许空闲配额借给繁忙项目:

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  name: project-1-queue
  namespace: ai-training-1
spec:
  clusterQueue: ml-gpu-cluster-queue
  # 允许借用其他项目未使用的配额
  maxResources:
    nvidia.com/gpu: 200  # 最多借用到200个GPU(自有100 + 借用100)
```

## 参考文档

- [Kueue官方文档](https://kueue.sigs.k8s.io/)
- [AWS HyperPod Kueue集成](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-task-governance.html)
- [Gang Scheduling原理](https://kueue.sigs.k8s.io/docs/concepts/workload/#gang-scheduling)
- [Kubeflow Training Operator + Kueue](https://www.kubeflow.org/docs/components/training/user-guides/kueue/)

## 维护清单

- [ ] 每月审查ClusterQueue配额使用情况
- [ ] 根据项目活跃度调整LocalQueue配额
- [ ] 监控优先级使用是否合理(避免滥用high)
- [ ] 定期清理已完成任务的Workload对象(自动GC)
- [ ] 更新ResourceFlavor以匹配集群节点变化
