# Infrastructure CDK Dev 环境验证计划

## Context

前序工作完成了 16 项审查问题修复 + 代码简化优化（共 23 个文件变更）。需要在真实 AWS dev 环境上验证这些变更能正确合成 CloudFormation 模板，并通过 `cdk diff` 确认变更范围合理、无意外副作用。

**AWS Account**: `897473508751` (来自 `cdk.context.json` 缓存)
**Region**: `us-east-1`
**环境**: dev (11 个 Stack)

---

## 验证步骤

### Step 1: 确认 AWS 凭证和身份

```bash
aws sts get-caller-identity
```

确认 account 为 `897473508751`，且角色有足够权限执行 `cdk synth` 和 `cdk diff`。

### Step 2: 本地质量门控（快速验证）

```bash
cd infrastructure/cdk
ruff check --exclude 'cdk.out*' . && pytest tests/ --tb=short -q
```

确认 234 测试通过 + lint 无错误（这是之前已验证的，此步为双重确认）。

### Step 3: CDK Synth（合成 dev 环境模板）

```bash
cdk synth --context env=dev --quiet
```

合成全部 11 个 dev Stack 的 CloudFormation 模板到 `cdk.out/`。此步骤会：
- 执行所有 CDK Nag 安全检查（AwsSolutionsChecks）
- 验证资源间引用的正确性
- 生成最终的 CloudFormation JSON

**预期结果**: 无错误输出，`cdk.out/` 中生成 11 个 `ai-platform-dev-*.template.json`。

### Step 4: CDK Diff（对比 dev 环境变更）

```bash
cdk diff --context env=dev 2>&1
```

对比当前代码生成的模板与 AWS 上已部署的 Stack 之间的差异。

**预期变更范围**（基于本轮修复内容）：

| Stack | 预期变更 |
|-------|---------|
| `ai-platform-dev-iam` | IRSA 条件新增、KMS 策略 resources 收窄、Nag 资源级抑制 |
| `ai-platform-dev-eks` | FSx CSI 策略替换、EKS Admin 角色条件新增 |
| `ai-platform-dev-storage` | S3 加密方式变更（KMS 强制）、CORS 配置（dev 无变化，仍为 `*`） |
| `ai-platform-dev-database` | Aurora Reader 移除、安全组规则变更（VPC CIDR → Private 子网） |
| `ai-platform-dev-fsx` | 安全组规则变更（VPC CIDR → Private 子网）、存储容量 10TiB → 1.2TiB |
| `ai-platform-dev-hyperpod-addons` | 废弃 Observability 输出移除 |
| `ai-platform-dev-observability` | 常量引用替换（功能不变）、CfnTag 方式变更 |
| `ai-platform-dev-sagemaker-hyperpod` | 路径引用替换（功能不变） |
| `ai-platform-dev-network` | 无变更 |
| `ai-platform-dev-alb` | 无变更 |
| `ai-platform-dev-application` | 无变更 |

**关注点**:
- FSx 容量从 10TiB 缩减到 1.2TiB — 如果 dev 环境已部署且存有数据，**缩容可能失败或导致数据丢失**，需确认
- Aurora Reader 移除 — 确认 dev 环境无读写分离依赖
- 安全组规则变更 — 确认 Private 子网 CIDR 覆盖所有实际的工作节点

### Step 5: 检查合成模板中的关键安全修复

```bash
# 验证 IRSA 条件约束生效
python3 -c "
import json
tpl = json.load(open('cdk.out/ai-platform-dev-iam.template.json'))
for k, v in tpl['Resources'].items():
    if v['Type'] == 'AWS::IAM::Role':
        policy = v.get('Properties', {}).get('AssumeRolePolicyDocument', {})
        for stmt in policy.get('Statement', []):
            if 'sts:AssumeRoleWithWebIdentity' in str(stmt):
                cond = stmt.get('Condition', {})
                assert cond, f'IRSA role {k} 缺少条件约束!'
                print(f'{k}: conditions OK')
"
```

---

## 关键文件

| 文件 | 用途 |
|------|------|
| `infrastructure/cdk/app.py` | CDK 入口，env/account/region 解析 |
| `infrastructure/cdk/cdk.json` | CDK 配置和 feature flags |
| `infrastructure/cdk/Makefile` | 快捷命令（`make synth-dev`, `make diff`） |
| `infrastructure/cdk/cdk.context.json` | AZ 查询缓存（含 account ID） |

---

## 注意事项

1. **不执行 `cdk deploy`** — 本次仅做 synth + diff 验证，不实际部署
2. 如果 `cdk diff` 显示 FSx 缩容变更，需评估是否跳过该 Stack 或先备份数据
3. `cdk synth` 需要网络访问（查询 AZ 信息），确保网络连通
