# CDK 项目代码优化计划

> 使用 code-simplifier 插件优化 AWS CDK IaC 项目

## 用户确认的决策

| 决策项 | 选择 |
|--------|------|
| GpuNodeGroupConstruct 处理 | **激活使用** - 在 EksStack 中调用 |
| Outputs 统一化 | **统一 + 删除 batch** - 所有 Stack 改用 create_output()，删除未用的 create_outputs_batch() |

## 项目概览

| 指标 | 数值 |
|------|------|
| **项目路径** | `infrastructure/cdk/` |
| **源代码** | ~6,040 行 (30 个 .py 文件) |
| **测试代码** | ~3,711 行 |
| **Stack 数量** | 9 个 |
| **代码质量评分** | B+ (良好，有优化空间) |

## 发现的问题

### P0 - 死代码 (高优先级)

| 文件 | 问题 | 行数 |
|------|------|------|
| `cdk_constructs/gpu_node_group.py` | 整个 Construct 未被任何 Stack 调用 | 378 行 |
| `utils/outputs.py` | `create_outputs_batch()` 定义但未使用 | ~60 行 |

### P1 - 代码重复 (中优先级)

| 位置 | 问题 | 预计节省 |
|------|------|---------|
| `utils/iam_helpers.py` | `create_tagged_role()` 与 `create_pod_identity_role()` 有 70% 代码重复 | ~50 行 |
| `utils/outputs.py` (46-48, 95-97) | kebab-case 转换逻辑重复 | ~10 行 |
| `utils/tagging.py` | `create_cfn_tags()` 与 `create_addon_tags()` 逻辑相似 | ~15 行 |

### P2 - 过长方法 (低优先级)

| Stack | 行数 | 建议 |
|-------|------|------|
| `alb_stack.py` | 596 | 可考虑拆分 WAF 规则配置 |
| `eks_stack.py` | 542 | 可提取 Add-ons 安装逻辑 |
| `fsx_stack.py` | 470 | 可提取监控告警配置 |

## 优化计划

### 阶段 1: 激活 GpuNodeGroupConstruct

**任务 1.1**: 在 EksStack 中集成 GpuNodeGroupConstruct

```
文件: stacks/compute/eks_stack.py
操作: 导入并调用 create_default_gpu_node_groups()
```

**修改内容**:
```python
# 1. 添加导入
from cdk_constructs.gpu_node_group import create_default_gpu_node_groups

# 2. 在 EksStack.__init__() 中调用
self._gpu_node_groups = create_default_gpu_node_groups(
    self,
    cluster=self._cluster,
    env_config=self.env_config,
)
```

**任务 1.2**: 统一 outputs 并删除死代码

```
文件: utils/outputs.py
操作: 删除未使用的 create_outputs_batch() (第 51-110 行)
```

**任务 1.3**: 统一所有 Stack 使用 create_output()

```
影响文件 (7 个 Stack):
- stacks/foundation/network_stack.py
- stacks/foundation/iam_stack.py
- stacks/data/database_stack.py
- stacks/data/storage_stack.py
- stacks/data/fsx_stack.py
- stacks/compute/eks_stack.py
- stacks/networking/alb_stack.py
```

**修改模式**:
```python
# 修改前
cdk.CfnOutput(self, "VpcId", value=vpc.vpc_id,
              description="VPC ID",
              export_name=f"{prefix}-vpc-id")

# 修改后
from utils.outputs import create_output
create_output(self, "VpcId", vpc.vpc_id, "VPC ID")
```

### 阶段 2: 消除代码重复

**任务 2.1**: 重构 `iam_helpers.py`

**当前问题**:
```python
# create_tagged_role() 和 create_pod_identity_role() 重复逻辑:
# - 角色创建
# - 标签应用
# - 策略附加
```

**重构方案**:
```python
# 提取共用的 _create_base_role() 内部函数
def _create_base_role(
    scope: Construct,
    role_id: str,
    assumed_by: iam.IPrincipal,
    description: str,
    env_config: EnvironmentConfig,
    managed_policies: list[iam.IManagedPolicy] | None = None,
) -> iam.Role:
    """基础角色创建逻辑 (内部使用)"""
    ...

def create_tagged_role(...) -> iam.Role:
    """对外接口 - 通用角色创建"""
    return _create_base_role(...)

def create_pod_identity_role(...) -> iam.Role:
    """对外接口 - Pod Identity 角色"""
    role = _create_base_role(...)
    # 添加 Pod Identity 特定配置
    return role
```

**任务 2.2**: 提取 kebab-case 转换工具函数

```python
# 新增到 utils/outputs.py 或单独的 utils/naming.py
def to_kebab_case(name: str) -> str:
    """将 PascalCase/camelCase 转换为 kebab-case"""
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()
```

**任务 2.3**: 合并 tagging.py 中的重复逻辑

```python
# 提取共用的标签字典构建逻辑
def _build_tags_dict(
    env_config: EnvironmentConfig,
    component: str,
    extra_tags: dict[str, str] | None = None,
) -> dict[str, str]:
    """构建标签字典 (内部使用)"""
    ...
```

### 阶段 3: 代码简化 (可选)

**任务 3.1**: 评估大型 Stack 拆分

| Stack | 建议拆分 | 原因 |
|-------|---------|------|
| `alb_stack.py` | WAF 规则 → 单独 Construct | 596 行，WAF 配置占 ~150 行 |
| `eks_stack.py` | Add-ons 安装 → 单独方法 | 542 行，可读性提升 |

**任务 3.2**: 补充 utils 单元测试 (可选)

```
创建文件:
- tests/unit/test_utils_iam_helpers.py
- tests/unit/test_utils_outputs.py
- tests/unit/test_utils_tagging.py
```

## 关键文件清单

### 需要修改的文件

| 文件 | 修改类型 | 优先级 |
|------|---------|--------|
| `cdk_constructs/gpu_node_group.py` | 删除或激活 | P0 |
| `utils/iam_helpers.py` | 重构消除重复 | P1 |
| `utils/outputs.py` | 添加工具函数/删除死代码 | P1 |
| `utils/tagging.py` | 提取共用逻辑 | P1 |

### 需要确认的文件 (只读)

| 文件 | 确认内容 |
|------|---------|
| `stacks/compute/eks_stack.py` | 确认是否需要 GpuNodeGroup |
| 所有 `stacks/*/*.py` | 确认 outputs 使用方式 |

## 验证方案

### 1. 代码质量检查

```bash
cd infrastructure/cdk

# Lint 和格式化
ruff check . && ruff format --check .

# 类型检查
mypy .
```

### 2. 单元测试

```bash
# 运行所有单元测试
pytest tests/unit -v

# 带覆盖率
pytest tests/unit --cov=. --cov-report=term-missing
```

### 3. 集成测试 (Stack 合成)

```bash
# 验证所有 Stack 能正常合成
pytest tests/integration/test_stack_synthesis.py -v

# 或直接使用 CDK
cdk synth --context env=dev
```

### 4. 差异检查

```bash
# 确保修改不影响生成的 CloudFormation 模板
cdk diff --context env=dev
```

## 执行顺序

```
1. 确认 GpuNodeGroupConstruct 是否需要 (需用户决策)
   ↓
2. 执行阶段 1 - 清理死代码
   ↓
3. 运行测试验证 (pytest + cdk synth)
   ↓
4. 执行阶段 2 - 消除代码重复
   ↓
5. 运行测试验证
   ↓
6. (可选) 执行阶段 3 - 代码简化
   ↓
7. 最终验证 (全部测试 + cdk diff)
```

## 已确认决策

1. **GpuNodeGroupConstruct**: ✅ 激活使用
   - 在 EksStack 中调用 `create_default_gpu_node_groups()`
   - 启用 P4D, P5, Trn1 GPU 节点组配置

2. **Outputs 统一化**: ✅ 统一 + 删除 batch
   - 所有 Stack 改用 `create_output()` 工具函数
   - 删除未使用的 `create_outputs_batch()`

## 预期收益

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 死代码行数 | ~438 行 | 0 行 |
| 重复代码 | ~75 行 | ~15 行 |
| 代码总行数 | ~6,040 行 | ~5,500 行 (预估 -9%) |
| 可维护性 | B+ | A- |
