# Infrastructure 多维度深度审查报告

> 审查日期: 2026-02-09
> 审查团队: 4 个专家 Agent (架构师 / 安全工程师 / FinOps+SRE / 质量工程师)

---

## 审查总览

| 维度 | 审查者 | 发现数 | CRITICAL | HIGH | MEDIUM |
|------|--------|--------|----------|------|--------|
| 架构设计 | architect-reviewer | 16 | 0 | 3 (P0) | 8 |
| 安全合规 | security-reviewer | 19 | 2 | 7 | 9 |
| 成本与运维 | finops-reviewer | 15 | 0 | 4 | 6 |
| 规范一致性 | quality-reviewer | 12 | 0 | 2 (P0) | 6 |

**跨维度共识** (多个审查者独立指出的问题):
1. FSx 单 AZ 部署风险 (架构 + 成本)
2. IAM 权限过宽 (安全 + 质量)
3. 监控告警缺失 (成本/运维 + 架构)
4. CDK Nag 抑制过于宽泛 (安全 + 质量)
5. 测试断言质量不足 (质量)

---

## 一、架构设计质疑 (architect-reviewer)

### P0 关键风险

**#8 FSx 单 AZ 部署** — `fsx_stack.py:214-217` 中 FSx 仅部署在第一个 Private 子网。PERSISTENT_2 不支持跨 AZ。单 AZ 故障将导致所有训练数据不可访问，违反宪法 "MUST 配置分层检查点存储" 的要求。

**#5 HyperPod 与 EKS 双重节点管理** — `sagemaker_hyperpod_stack.py` 定义 HyperPod Instance Group，`eks_stack.py:83-90` 又创建 EKS Managed Node Group。两套节点共存于同一 VPC，缺少明确的 nodeSelector/affinity 区分 Pod 调度目标。

**#14 AZ 故障无恢复策略** — FSx (单 AZ) + Dev NAT Gateway (1 个) + HyperPod Controller (1 个实例) 构成多个 AZ 级单点故障，无故障转移文档。

### P1 重要问题

- **#11 VPC CIDR 千节点不足**: Prefix Delegation 启用后每节点消耗 ~110 IP，1000 节点需 ~110,000 IP，超 /16 容量
- **#7 HyperPod Add-on 无版本锁定**: 生产环境每次部署可能安装不同版本
- **#1 L3 串行链 45-60 分钟**: EKS→HyperPod→Addons 串行部署，回滚代价高
- **#6 HyperPod vs EKS 实例类型不一致**: HyperPod 配 g5，EKS 配 p4d/p5，缺联动

### P2 架构债务

- KMS Key 与 IAM Stack 耦合 (应独立)
- ApplicationStack 过薄 (仅 ECR，缺应用部署集成)
- 11 Stack 的 CloudFormation 输出量级隐患

---

## 二、安全审查 (security-reviewer)

### CRITICAL (2 项)

**F-IAM-01: IRSA 信任策略空条件 (Confused Deputy)** — `iam_stack.py:184-188` 中 `conditions={}` 允许 EKS 集群内任何 Pod assume 训练执行角色和后端服务角色。攻击者仅需在集群创建 Pod 即可获取 S3/SageMaker/SecretsManager 权限。

**F-IAM-02: FSx CSI 使用 AmazonFSxFullAccess** — `eks_stack.py:264` 授予 CSI Driver 完整 FSx 操作权限（含 DeleteFileSystem），实际仅需 Describe 权限。

### HIGH (7 项)

| ID | 问题 | 文件 |
|----|------|------|
| F-IAM-03 | EKS Admin 使用 AccountRootPrincipal | `eks_stack.py:117` |
| F-IAM-04 | KMS 策略 resources=["*"] | `iam_stack.py:393` |
| F-NET-01 | S3 CORS `allowed_origins=["*"]` | `storage_stack.py:194` |
| F-DATA-01 | S3 加密回退到 S3_MANAGED | `storage_stack.py:107-112` |
| F-COMP-01 | 缺少 CloudTrail/GuardDuty/SecurityHub | 全局 |
| F-COMP-02 | S3 无 Server Access Logging | `nag_suppressions.py:66-69` |
| F-NAG-01 | Stack 级 Nag 抑制过宽 | `nag_suppressions.py:29-37` |

### MEDIUM (9 项)

包括: SageMaker SP 无条件约束、ALB 无访问日志、EFA NetworkPolicy 全端口开放、数据库凭据无自动轮换、platform-admin 超级权限、tenant-admin 可操作 Secrets、WAF 默认关闭、VPC Endpoint 无 Policy、TODO 式 Nag 抑制积累。

### 安全亮点 (做得好的)

VPC 三层隔离、EKS Private Endpoint、Default Deny NetworkPolicy、IMDSv2 强制、KMS 密钥轮换、S3 Block Public Access + Enforce SSL、RDS IAM 认证 + Proxy TLS、CDK Nag 全环境启用。

---

## 三、成本与运维审查 (finops-reviewer)

### GPU 成本失控风险

- **Prod 理论最大**: 99 GPU 节点 = **$5,036/h = $3.6M/月** — 无 AWS Budgets 告警实现 (仅文档)
- **Spot GPU 不可行**: HyperPod 不原生支持 Spot，`nvidia-a100-40gb-spot` ResourceFlavor 定义存在但无法实际使用
- **Kueue 配额与自动伸缩冲突**: nominalQuota=64 GPU 但 min_size=0，冷启动 5-10 分钟

### Dev 环境月度浪费 ~$1,400

| 资源 | 当前成本/月 | 优化后/月 | 节省 |
|------|-----------|----------|------|
| FSx (10 TiB PERSISTENT_2) | $1,485 | $174 (1.2 TiB SCRATCH_2) | $1,311 |
| Aurora (Writer+Reader) | $150 | $87 (仅 Writer) | $63 |
| VPC Endpoints (11 个) | $79 | $27 (3 个) | $52 |
| **合计 (不含 GPU)** | **$1,756** | **$330** | **$1,426** |

### Prod FSx 过度配置

初始 100 TiB = ~$14,850/月。建议从 20 TiB 开始 (~$2,970/月)，按需扩容，节省 ~$11,880/月。

### 运维关键缺失

- **监控告警几乎为零**: AMP 只收集数据，无 Grafana/CloudWatch Alarms/SNS 通知
- **无 CI/CD Pipeline**: 11 Stack 手动部署，无审计轨迹、无 approval gate
- **无 DR 计划**: RTO/RPO 未定义，无跨区域备份/复制配置
- **Aurora Serverless v2 不支持暂停**: min_acu=0.5 注释"可暂停"是误导

---

## 四、规范一致性与测试质量 (quality-reviewer)

### Spec-Implementation 缺口 (~30%)

| 缺失的 FR 实现 | 严重度 |
|----------------|--------|
| FR-004 PriorityClass (high/medium/low) 配置 | P1 |
| FR-012 Spaces Add-on | P1 |
| FR-021 NetworkPolicy CDK 管理 | P1 |
| FR-025 GitOps (ArgoCD) | P2 |
| Elastic Agent Add-on | P1 |

### 测试质量问题

**Snapshot 测试仅比较摘要** — `test_snapshot.py` 的 `_normalize_template()` 只保留资源类型和数量，属性级变更（如 KMS 轮换关闭、安全组全端口开放）完全无法检测。

**EKS Stack 断言过弱** — `test_eks_stack.py` 大量使用 `assert len(xxx) >= 1`，未验证 Kubernetes 版本、端点配置、加密等关键属性。

**CDK Nag 安全合规测试完全缺失** — checklist.md 明确要求，但零实现。

**@pytest.mark.unit 标记缺失** — pyproject.toml 定义了 marker 但测试文件未标注，导致 `-m unit` 过滤收集不到测试。

### 覆盖率 95% 的含义

行覆盖率达标，但:
- 弱断言贡献了大量"有执行无验证"的覆盖
- `utils/` 未纳入覆盖率统计源
- 关键错误处理路径 (WAF、FSx 性能配置) 在 miss 行中

---

## 五、跨维度优先级矩阵

### 立即修复 (P0)

| # | 问题 | 维度 | 影响 |
|---|------|------|------|
| 1 | IRSA 空条件 confused deputy | 安全 | 集群内任何 Pod 可冒充训练角色 |
| 2 | FSx CSI AmazonFSxFullAccess | 安全 | CSI Driver 可删除生产文件系统 |
| 3 | AWS Budgets 告警未实现 | 成本 | GPU 成本可达 $3.6M/月无预警 |
| 4 | CDK Nag 合规测试缺失 | 质量 | 安全门禁形同虚设 |

### 短期修复 (P1, 1-2 周)

| # | 问题 | 维度 |
|---|------|------|
| 5 | S3 CORS 通配符 origin | 安全 |
| 6 | CloudTrail/GuardDuty/SecurityHub | 安全 |
| 7 | S3 Server Access Logging | 安全 |
| 8 | HyperPod Add-on 版本锁定 | 架构 |
| 9 | Dev FSx 缩减到 1.2 TiB | 成本 |
| 10 | Prod FSx 初始 20 TiB | 成本 |
| 11 | Snapshot 测试重写为完整模板比较 | 质量 |
| 12 | EKS Stack 断言加强 | 质量 |

### 中期修复 (P2, 1-3 月)

| # | 问题 | 维度 |
|---|------|------|
| 13 | FSx 单 AZ 恢复策略文档 | 架构 |
| 14 | CI/CD Pipeline 落地 | 运维 |
| 15 | Grafana + CloudWatch Alarms | 运维 |
| 16 | DR 计划 (RTO/RPO) | 运维 |
| 17 | VPC Endpoint Policy | 安全 |
| 18 | 数据库凭据自动轮换 | 安全 |
| 19 | PriorityClass / Spaces Add-on 补全 | 规范 |
| 20 | @pytest.mark.unit 标记补全 | 质量 |
