# HyperPod Task Governance 配置指南

> **适用**: EKS Add-on v1.1.3+, Kueue v0.12.0+ | **原则**: SDK-First (spec.md §抽象层使用决策指南)

## 配置优先级

1. **Task Governance API** (Console/CLI) ← 首选
2. **K8s 原生** (kubectl) ← API 无法解决时
3. **直接修改 CRD** ← 最后手段，⚠️ 可能被覆盖

## 1. 安装

```bash
# 安装
aws eks create-addon --region $REGION --cluster-name $CLUSTER \
  --addon-name amazon-sagemaker-hyperpod-taskgovernance

# 验证
aws eks describe-addon --region $REGION --cluster-name $CLUSTER \
  --addon-name amazon-sagemaker-hyperpod-taskgovernance
```

**前置条件**: K8s >= 1.30 | HyperPod 节点已存在 | 无独立 Kueue

**自动创建资源**: `ClusterQueue` `LocalQueue` `WorkloadPriorityClass` `ResourceFlavor` (均由 TG 托管)

## 2. 策略配置 (Console)

**路径**: SageMaker Console → HyperPod → Cluster → **Policies**

| 策略 | 配置项 | 选项/示例 |
|-----|-------|----------|
| **优先级** | Idle compute | FCFS / Fair-share / Task prioritization |
| | Priority classes | high(1000) / medium(500,default) / low(100) |
| **配额** | Team | team-nlp |
| | Fair-share weight | 100 |
| | Preemption/Lending/Borrowing | Enabled |
| | Borrow limit | 200% |

## 3. 优先级

**CLI**:
```bash
hyp create hyp-pytorch-job --priority high-priority \
  --namespace hyperpod-ns-$TEAM --queue-name hyperpod-ns-$TEAM-localqueue ...
```

**YAML**:
```yaml
metadata:
  labels:
    kueue.x-k8s.io/queue-name: hyperpod-ns-team-nlp-localqueue
    kueue.x-k8s.io/priority-class: high-priority  # ⚠️ 非 Pod.priorityClassName
```

## 4. 抢占

| 前提 | 要求 |
|-----|------|
| Cohort | 两个 ClusterQueue 在同一 Cohort |
| Quota | 总 nominal ≤ 物理资源 |
| 策略 | 高优先级: nominal=实际,borrow=0; 低优先级: nominal=0,borrow=实际 |

⚠️ `DontLend` 策略会创建独立 Cohort，阻止抢占

## 5. TAS (Topology-Aware Scheduling)

**默认禁用**，需工作负载级别启用 | 要求 v1.2.2-eksbuild.1+

**CLI**: `--preferred-topology-label topology.k8s.aws/network-node-layer-3`

**YAML**:
```yaml
annotations:
  kueue.x-k8s.io/podset-required-topology: "topology.k8s.aws/network-node-layer-3"
  # 或 podset-preferred-topology (软约束)
```

| 拓扑层级 | 延迟 |
|---------|------|
| layer-1 | 高 |
| layer-2 | 中 |
| layer-3 | 低 ← 推荐 |
| ultraserver-id | 极低 |

## 6. CRD 参考 (仅供理解)

> ⚠️ 生产环境通过 Task Governance API 配置，手动修改可能被覆盖

**ClusterQueue**:
```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
spec:
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: nvidia-a100-40gb
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 8
              borrowingLimit: 16
              lendingLimit: 4
  cohort: hyperpod-default-cohort
  preemption:
    reclaimWithinCohort: Any
    borrowWithinCohort: { policy: LowerPriority }
  fairSharing: { weight: 100 }
```

**LocalQueue**:
```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  namespace: hyperpod-ns-team-nlp
spec:
  clusterQueue: hyperpod-team-nlp-clusterqueue
```

## 7. 故障排查

| 问题 | 原因 → 解决 |
|-----|------------|
| Pending | 配额不足/TAS约束 → 检查配额，放宽TAS |
| 抢占不生效 | 不同Cohort → 确保同一Cohort |
| TAS失败 | 约束过严 → 用 preferred-topology |
| 配置被覆盖 | 手动修改CRD → 用API配置 |

**诊断**:
```bash
kubectl get workloads -n $NS                    # Workload状态
kubectl get clusterqueues -o wide               # CQ状态
kubectl describe localqueue $LQ -n $NS          # 队列事件
kubectl logs -n kueue-system -l app.kubernetes.io/name=kueue  # Kueue日志
```

## 参考

- [Task Governance 官方文档](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html)
- [TAS 配置](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance-tasks-scheduling.html)
- [最佳实践](https://aws.amazon.com/blogs/machine-learning/best-practices-for-amazon-sagemaker-hyperpod-task-governance/)
- [Kueue 文档](https://kueue.sigs.k8s.io/)
