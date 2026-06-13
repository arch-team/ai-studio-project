> **职责**: UX 文案规范 - 术语映射、状态标签、文案模式与中文排版

# UX 文案规范 (UX Writing Standards)

> **适用范围**: 所有 features 页面的用户可见文案（标题、按钮、状态、空态、错误、表单提示、确认对话框）
> **基线依据**: 2026-06-13 baseline 审计——状态枚举中英混用（F-031）、术语跨页不一致
> **核心命题**: 同一概念在全站只有一种表达。术语、动词、状态名词、标点统一，是商用化品质的下限。

---

## 0. 速查卡片

> Claude 生成页面文案时优先查阅此章节

### 0.1 实体术语映射表（与根 [CLAUDE.md](../../../CLAUDE.md) 术语标准一致）

| 中文术语（UI 展示） | Python 类 | 数据库表 | API 路径 |
|---------------------|-----------|----------|----------|
| **训练任务** | `TrainingJob` | `training_jobs` | `/training-jobs` |
| **数据集** | `Dataset` | `datasets` | `/datasets` |
| **检查点** | `Checkpoint` | `checkpoints` | `/checkpoints` |
| **模型** | `Model` | `models` | `/models` |
| **资源配额** | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |
| **开发空间** | `Space` | `development_spaces` | `/spaces` |

**铁律**: UI 文案统一用上表「中文术语」列。禁止在界面混用英文实体名（如显示 `TrainingJob`、`Space`）或同义词漂移（"作业/任务"、"工作区/开发空间"二选一，全站只用一种）。

### 0.2 UI 场景术语统一表

**按钮动词**（动作语义固定，不同义替换）:

| 动词 | 语义 | ✅ 用 | ❌ 勿用 |
|------|------|------|---------|
| **创建** | 新建一个实体（进入表单/向导） | 创建训练任务、创建开发空间 | 新增、添加、新建（择一即"创建"） |
| **提交** | 把已填表单发往后端 | 提交、提交任务 | 确定、保存（提交语义专用） |
| **保存** | 持久化编辑（已存在实体的修改） | 保存、保存更改 | 提交、应用 |
| **取消** | 放弃当前操作/关闭弹窗 | 取消 | 返回、关闭（弹窗放弃统一"取消"） |
| **删除** | 移除实体（危险操作，需二次确认） | 删除、确认删除 | 移除、清除（删除语义专用） |
| **重试** | 失败后重新发起请求 | 重试 | 刷新、再试一次 |

**状态名词**（统一走 `{ENTITY}_STATUS_LABELS`，见 §1）:

| 英文枚举 | ✅ 中文标签 | 出现模块 |
|----------|-----------|---------|
| `running` | 运行中 | training / spaces |
| `completed` | 已完成 | training |
| `failed` | 已失败 / 失败 | training（已失败）/ spaces（失败）※按各模块 LABELS 既有值 |
| `paused` | 已暂停 | training |
| `preempted` | 被抢占 | training |
| `submitted` | 已提交 | training |

> ⚠️ 各模块 LABELS 的具体措辞（如 training 用「已失败」、spaces 用「失败」）以代码中既有定义为准，**不在本文件强行统一**；本表仅示意枚举→中文的映射关系。新增枚举值时沿用"已+动词"风格（已完成/已归档/已注册）。

### 0.3 陷阱 ⚠️

- ❌ 页面直接渲染英文枚举值 `{job.status}` → ✅ 走 `JOB_STATUS_LABELS[job.status]`（F-031）
- ❌ 同一动作在不同页面用不同动词（一处"新建"一处"创建"） → ✅ 全站锁定 §0.2 动词
- ❌ 错误文案只说"出错了" → ✅ 说清"发生什么 + 怎么办"（§2.2）
- ❌ 删除确认只问"确定吗" → ✅ 说明后果"此操作不可撤销"（§2.3）
- ❌ 中英文紧贴无空格 `训练任务API` → ✅ `训练任务 API`（§3.2）
- ❌ 半角标点混入中文 `任务创建成功!` → ✅ 全角 `任务创建成功！`（§3.1）

---

## 1. 状态标签常量 `{ENTITY}_STATUS_LABELS`

> 本章固化**既有约定**，不是新设计。全站 8 处状态映射均遵循此模式。

### 1.1 模式定义

每个模块在 `features/{module}/types/index.ts` 的 **UI Helper Constants** 区定义一个 `Record<Status, string>` 常量，把英文状态枚举映射为中文展示文案：

```typescript
// features/training/types/index.ts（真实代码）
export type JobStatus =
  | 'submitted' | 'running' | 'paused' | 'preempted' | 'completed' | 'failed';

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  submitted: '已提交',
  running: '运行中',
  paused: '已暂停',
  preempted: '被抢占',
  completed: '已完成',
  failed: '已失败',
};
```

**命名约定**: 常量名 = `{ENTITY}_STATUS_LABELS`（UPPER_SNAKE_CASE），类型 = `Record<{Entity}Status, string>`，值为中文。

**现存清单**（均为同一形式，不要新造写法）:

| 常量 | 模块 | 类型 |
|------|------|------|
| `JOB_STATUS_LABELS` | training | `Record<JobStatus, string>` |
| `MODEL_STATUS_LABELS` | models | `Record<ModelStatus, string>` |
| `SPACE_STATUS_LABELS` | spaces | `Record<SpaceStatus, string>` |
| `DATASET_STATUS_LABELS` | datasets | `Record<DatasetStatus, string>` |
| `USER_STATUS_LABELS` | admin | `Record<UserStatus, string>` |
| `CLUSTER_STATUS_LABELS` / `NODE_STATUS_LABELS` | monitoring | `Record<..., string>` |
| `REGISTRY_SYNC_STATUS_LABELS` | models | `Record<RegistrySyncStatus, string>` |

> 配套的 `{ENTITY}_STATUS_COLORS`（`Record<Status, Cloudscape 色值>`）与 LABELS 成对出现，供 `<StatusIndicator>` / `<Badge>` 着色，命名同构。

### 1.2 铁律 🔴

**所有状态展示必须走 `{ENTITY}_STATUS_LABELS` 映射，禁止页面直接渲染英文枚举值。**

```tsx
// ✅ 正确 — 经 LABELS 映射，配合 StatusIndicator（颜色+图标+文字，见 accessibility.md §5）
import { JOB_STATUS_LABELS, JOB_STATUS_COLORS } from '@features/training';
<StatusIndicator type={JOB_STATUS_COLORS[job.status]}>
  {JOB_STATUS_LABELS[job.status]}
</StatusIndicator>

// ❌ 错误 — 裸渲染英文枚举值，用户看到 running/completed（F-031 根因）
<span>{job.status}</span>
<Badge>{job.status}</Badge>
```

> ⚠️ 待改项：确保所有状态展示走 LABELS（F-031）。model-versions 页当前直接显示英文 `deployed/registered/archived/failed`，与 list/detail 页的中文标签跨页不一致，阶段 4 修复时改为走 `MODEL_STATUS_LABELS`。

---

## 2. 文案模式

### 2.1 空状态文案

空态需「中性说明 + 引导主操作 CTA」，描述"暂无 X"，不暗示故障（结构呈现见 [interaction-states.md](interaction-states.md) §3）。

| ❌ 坏 | ✅ 好 |
|------|------|
| 仅一行"暂无数据"，无下一步 | `暂无数据集` + 主按钮`注册第一个数据集` |
| "列表为空" | `还没有训练任务` + 主按钮`创建训练任务` |

```tsx
// CTA 文案模式：「动词 + 第一个 + 实体」或「动词 + 实体」
<Box variant="strong">暂无数据集</Box>
<Button variant="primary" onClick={handleCreate}>注册第一个数据集</Button>
```

### 2.2 错误信息文案

错误文案讲清两件事：**发生了什么** + **现在能怎么办**（错误态结构、重试入口见 [interaction-states.md](interaction-states.md) §1）。

| ❌ 坏 | ✅ 好 |
|------|------|
| `出错了` | `加载训练任务失败，请检查网络后重试。` |
| `Error 500` | `服务暂时不可用，请稍后重试。` |
| `任务不存在`（无下一步） | `未找到该训练任务，它可能已被删除。`（配返回出口） |
| `操作失败` | `提交失败：实例配额不足，请调整节点数或申请扩容。` |

**措辞要点**:
- 标题简短定性（`加载失败` / `任务不存在`），正文给原因或动作建议
- 优先用 `error?.message`，缺省回退`发生未知错误，请稍后重试。`
- 不暴露堆栈、HTTP 状态码原文、内部变量名

### 2.3 确认对话框文案

危险操作（删除任务、停止运行任务、删除数据集、清空检查点、重置配额）的确认弹窗必须**说明后果**，不可只问"确定吗"（弹窗交互结构见 [component-design.md](component-design.md) §4.3）。

| ❌ 坏 | ✅ 好 |
|------|------|
| 标题`确认` / 正文`确定吗？` | 标题`确认删除训练任务` / 正文`此操作不可撤销，任务及其检查点将被永久删除。` |
| `停止任务？` | `停止后任务无法恢复运行，已产生的费用不退还。确认停止？` |

**模式**: `<后果陈述> + 确认问句`；不可逆操作显式写「此操作不可撤销」，高破坏性操作要求输入实体名二次确认。

### 2.4 表单帮助文本

Cloudscape `<FormField>` 有两个文案位，**分工不同，勿混用**:

| 文案位 | 用途 | 内容 | 示例 |
|--------|------|------|------|
| `description` | 字段**说明**：这是什么、为何要填 | 解释语义、给背景 | `用于区分同一项目下的不同实验` |
| `constraintText` | 字段**约束**：格式/范围/必填 | 规则、限制、必填标记 | `1-128 字符，仅限字母、数字、连字符` |

```tsx
// ✅ description 说语义，constraintText 说约束
<FormField
  label="任务名称"
  description="训练任务的唯一标识，创建后不可修改"
  constraintText="必填，1-128 字符，仅限字母、数字和连字符"
>
  <Input value={name} onChange={({ detail }) => setName(detail.value)} />
</FormField>

// ❌ 把约束塞进 description、或两者内容重复
<FormField label="任务名称" description="必填，1-128 字符">...</FormField>
```

> 校验失败的错误文案走 `errorText`（Zod schema message，见 [state-management.md](state-management.md) §3），措辞同 §2.2：`请输入任务名称`、`名称不超过 128 字符`。

---

## 3. 中文排版规范

### 3.1 标点符号

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 中文语境用全角标点 | `任务创建成功！` `确认删除？` | `任务创建成功!` `确认删除?` |
| 中文逗号/句号全角 | `加载失败，请重试。` | `加载失败,请重试.` |
| 中文括号全角 | `（可选）` | `(可选)` |
| 省略号用全角 | `加载中……` 或 `加载中...`（统一其一） | 混用 |
| 代码/路径/英文短语内保持半角 | `仅限字母、数字和连字符（a-z, 0-9, -）` | 把代码标点改全角 |

### 3.2 中英文之间加空格

中文与英文单词/数字之间插入一个半角空格，提升可读性:

| ✅ 正确 | ❌ 错误 |
|--------|--------|
| `训练任务 API` | `训练任务API` |
| `PyTorch DDP 分布式策略` | `PyTorchDDP分布式策略` |
| `共 12 个模型` | `共12个模型` |
| `Amazon S3 存储` | `Amazon S3存储` |

> 例外：紧邻全角标点时不额外加空格（`使用 API。` 而非 `使用 API 。`）。

### 3.3 数字与单位

数字与单位之间加空格，单位用中文或标准缩写，全站一致:

| 场景 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| 节点数 | `4 节点` | `4节点` / `4个节点`（统一"N 节点"） |
| GPU 数 | `32 GPU` | `32GPU` |
| 百分比 | `62%`（紧贴，无空格） | `62 %` |
| 存储容量 | `128 GB` / `2 TB` | `128GB` |
| 时长 | `3 小时 20 分钟` | `3小时20分钟` |
| 金额 | `$1,234.56` / `¥8,900` | `$ 1234.56` |

> 百分号 `%` 紧贴数字（`62%`）；其余物理单位前留空格（`128 GB`）。

---

## 4. 语气基准

平台面向工程师，文案保持**专业、直接、无废话**:

| 维度 | 要求 |
|------|------|
| **专业** | 用准确术语，不口语化、不卖萌；不用营销辞令（"极速""强大""完美") |
| **直接** | 一句话说清，主语动词明确；动作类文案以动词开头 |
| **无废话** | 删冗余客套，不重复界面已有信息；不用"请您""敬请""非常抱歉" |

**改写对照**:

| ❌ 冗长 / 客套 | ✅ 精炼 / 直接 |
|---------------|---------------|
| `非常抱歉，您的训练任务由于某些原因未能成功创建，请您稍后再试一次。` | `任务创建失败，请稍后重试。` |
| `您确定真的要删除这个训练任务吗？删除之后就找不回来了哦。` | `此操作不可撤销，任务及其检查点将被永久删除。确认删除？` |
| `欢迎使用！当前这里暂时还没有任何数据集，您可以点击下方按钮来注册您的第一个数据集。` | `暂无数据集，注册第一个数据集开始使用。` |

---

## 已知差距清单

> 本规范定义目标范式；以下为存量页面与目标的差距，由阶段 4 修复任务按编号消化。

| 编号 | 维度 | 差距 | 涉及页面 |
|------|------|------|---------|
| F-031 | 状态标签映射 | 状态枚举中英不一致：model-versions 页直接显示英文 `deployed/registered/archived/failed`，list/detail 页用中文 LABELS，同一术语跨页混用 → 统一走 `MODEL_STATUS_LABELS` | models/model-versions |
