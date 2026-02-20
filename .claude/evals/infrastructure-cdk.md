## EVAL: infrastructure-cdk
Created: 2026-02-20
Last Check: 2026-02-20
Module: infrastructure/cdk/
Phase: 1-2 (Setup + Foundational)
Tasks: T008a-T008i

### Capability Evals

#### VPC Stack (T008b)
- [x] VPC CIDR 默认 10.0.0.0/16，支持通过 CDK context 配置
- [x] 三层子网隔离: 公有/私有应用层/私有数据层
- [x] 3 个可用区部署
- [x] NAT Gateway 在 2 个 AZ 部署 (成本优化)
- [x] VPC 端点正确创建: S3 Gateway, ECR, CloudWatch, STS, SageMaker API, EFS
- [x] 部署模式支持 single-az/multi-az/hybrid

#### Database Stack (T008b)
- [x] Aurora MySQL Serverless v2 正确配置 (ACU 0.5-16)
- [x] 自动备份保留期 7 天
- [x] 多可用区部署，故障转移 <30 秒
- [x] RDS Proxy 连接池正确配置

#### Storage Stack (T008b)
- [x] S3 存储桶创建: datasets, models, checkpoints
- [x] 所有存储桶启用 SSE-KMS 默认加密
- [x] 所有存储桶 Bucket Policy 拒绝非 HTTPS 传输
- [x] 所有存储桶启用版本控制

#### IAM Stack (T008b + T008c-3)
- [x] EKS 节点角色遵循最小权限原则
- [x] 训练任务 Pod IAM 角色限定到训练相关 bucket
- [x] Service Account 映射正确 (IRSA)
- [x] RBAC ClusterRole 正确定义 (admin/project_manager/engineer/viewer)

#### HyperPod EKS 集群 (T008c-1/2/3)
- [x] EKS 1.32+ 集群创建成功
- [x] GPU 节点组配置 (p4d/p5/trn1)
- [x] Auto Scaling 策略: 扩容 Pending >0 持续 5 分钟
- [x] Auto Scaling 策略: 缩容 GPU 利用率 <20% 持续 15 分钟
- [x] EFA 高性能网络启用
- [x] Pod Security Standards (restricted 模式) 启用
- [x] EKS Add-ons: EBS CSI, FSx CSI, VPC CNI 安装

#### HyperPod Add-ons (T008d)
- [x] Training Operator Add-on 安装，PyTorchJob CRD 注册
- [x] Task Governance Add-on 安装，ClusterQueue/LocalQueue 状态 Active
- [x] PriorityClass 三级配置 (low:100, medium:500, high:1000)
- [x] Observability Add-on 安装，Prometheus/Grafana 可访问
- [x] Spaces Add-on 安装，Spaces CRD 注册

#### FSx for Lustre (T008e)
- [x] Persistent_2 部署类型创建
- [x] 500 MB/s/TiB 吞吐量配置
- [x] S3 Data Repository Association 自动同步
- [x] FSx CSI Driver StorageClass 创建
- [x] 单客户端吞吐量 >= 5GB/s

#### ALB Stack (T008i)
- [x] Application Load Balancer 创建在公有子网
- [x] HTTPS 监听器 (443) 绑定 ACM 证书
- [x] TLS 1.2+ 强制 (禁用 TLS 1.0/1.1)
- [x] HTTP -> HTTPS 自动重定向

#### 基础设施验证 (T008g)
- [x] EKS 集群状态健康，所有节点 Ready
- [x] GPU 可见性和 CUDA 版本正确
- [x] 测试 PyTorchJob 成功执行
- [x] Prometheus 指标可查询
- [x] FSx PVC 挂载和读写性能测试通过
- [x] Pod 到 Internet/PrivateLink 连通性正常
- [x] ALB HTTPS 端点可访问，TLS >= 1.2

### Regression Evals
- [x] CDK 合成 (cdk synth) 无错误
- [x] CDK 差异检查 (cdk diff) 无意外变更
- [x] Stack 间依赖关系正确 (Network -> Data -> Storage -> Compute)
- [x] 所有 Stack 测试通过
- [x] CloudFormation 输出值正确导出

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- CDK 单元测试全部通过
- FSx 吞吐量 >= 5GB/s
- ALB TLS >= 1.2
