# PR Review 检查清单

> **职责**: PR Review 检查清单的**单一真实源**，涵盖架构、设计、安全、测试、部署和成本检查项。

---

## 分层与架构

- [ ] Stack 放在 `stacks/` 对应子目录
- [ ] 自定义 Construct 放在 `cdk_constructs/`
- [ ] 新 Stack 已添加到 `CLAUDE.md` 的 Stack 分层表
- [ ] 没有跨 Stack 的直接资源引用 (`Fn.import_value` 禁止)
- [ ] Stack 依赖方向正确 (L5 → L4 → L3 → L2 → L1)
- [ ] 通过构造函数参数传递资源 (依赖注入)

详见 [architecture.md](architecture.md)

---

## Construct 设计

- [ ] Props 使用 `@dataclass(frozen=True)` 定义
- [ ] 可选参数有合理默认值
- [ ] 暴露必要的公开属性 (`@property`)
- [ ] 公开方法和属性有类型注解
- [ ] 配置项 ≥ 5 个时使用 Props dataclass

详见 [construct-design.md](construct-design.md)

---

## 安全

- [ ] 使用 Grant 方法而非手动 IAM 策略
- [ ] 敏感信息存储在 Secrets Manager
- [ ] S3 Bucket: `block_public_access=BLOCK_ALL`, `enforce_ssl=True`
- [ ] 数据层使用 `PRIVATE_ISOLATED` 子网
- [ ] KMS Key 启用 `enable_key_rotation=True`
- [ ] EC2 强制 `require_imdsv2=True`
- [ ] CDK Nag 检查通过 (staging/prod)
- [ ] 没有 `actions=["*"]` 或 `resources=["*"]`

详见 [security.md](security.md)

---

## 测试

- [ ] 每个 Stack/Construct 有对应测试
- [ ] 关键属性有 Fine-grained 断言 (`has_resource_properties`)
- [ ] 覆盖率达标 (`stacks/` ≥90%, `cdk_constructs/` ≥85%)
- [ ] 测试使用 `@pytest.mark.unit` 标记
- [ ] 没有 `@pytest.mark.skip` 跳过测试

详见 [testing.md](testing.md)

---

## 部署

- [ ] 环境配置使用 CDK Context (`--context env=dev`)
- [ ] 有适当的 RemovalPolicy (见 [deployment.md](deployment.md))
- [ ] `cdk diff` 确认变更范围
- [ ] 有回滚计划
- [ ] HyperPod 相关: Helm Chart 超时设置 ≥ 15 分钟

详见 [deployment.md](deployment.md)

---

## 成本

- [ ] 所有资源有成本标签 (`Project`, `Environment`, `CostCenter`, `ManagedBy`)
- [ ] Dev 环境使用最小规格
- [ ] S3 有生命周期规则
- [ ] CloudWatch Logs 有保留期限 (Dev: 1 周, Prod: 1 年)
- [ ] GPU 实例成本已评估 (p4d ~$32/h, p5 ~$98/h)

详见 [cost-optimization.md](cost-optimization.md)

---

## 代码质量

- [ ] 无硬编码的账户 ID 或区域
- [ ] `cdk.context.json` 未被提交
- [ ] ruff check 通过 (无 lint 错误)
- [ ] mypy 通过 (无类型错误)
- [ ] 导入顺序正确 (标准库 → 第三方 → 项目内部)

详见 [code-style.md](code-style.md)

---

## 预提交一键验证

```bash
ruff check . && ruff format --check . && mypy . && pytest -m unit --cov=stacks --cov=cdk_constructs
```
