> **职责**: 交互状态规范 - 错误/加载/空/成功四态完整性与 error 态铁律

# 交互状态规范 (Interaction States Standards)

> **适用范围**: 所有 features 页面（List / Detail / Form / Dashboard）的数据驱动状态呈现
> **基线依据**: 2026-06-13 baseline 审计——error 态问题占 P0 半数（F-001/004/005/006/007/008/011/014），空态缺 CTA（F-041）
> **核心命题**: 任何一个数据消费界面，都必须显式处理 **default / loading / empty / error** 四种状态，缺一即视为缺陷。

---

## 0. 速查卡片

> Claude 生成页面代码时优先查阅此章节

### 0.1 四态决策表（按页面类型）

| 页面类型 | default | loading | empty | error |
|---------|:-------:|:-------:|:-----:|:-----:|
| **List 列表页** | Table 渲染数据 | Table `loading` 属性 | Table `empty` 槽（**带 CTA**） | 顶部内联 `Alert type="error"` + 重试（骨架保留） |
| **Detail 详情页** | 实体内容区块 | `PageLayout` 骨架内 Spinner | 子区块空文案（如"暂无检查点"） | `PageLayout` 骨架内 `InlineErrorState`（固定标题 + 重试/返回） |
| **Form 表单页** | 字段可编辑 | 提交时按钮 `loading` + 禁用 | （表单无 empty 态） | 字段级 `errorText` + 提交失败 `Alert`/`Flashbar` |
| **Dashboard 仪表盘** | 指标卡 + 图表 | 各区块骨架占位 | "暂无数据"区块 | **整体降级报错**，禁止把失败伪装成"0/空/全绿"（F-001/030） |

**核心铁律**: 多 query 页面中，**任一子资源失败都要显式报错**，不得静默降级为 `0` 或 `[]`（F-006）。

### 0.2 陷阱 ⚠️

- ❌ error 时 `if (error) return <Container>加载失败</Container>` 裸容器塌缩，丢失标题/面包屑/筛选区（F-007/011/014/023/025）→ ✅ 保留 `PageLayout` 骨架再报错
- ❌ `data ?? []` / `data ?? 0` 把加载失败静默降级为"无数据"（F-001/006/024）→ ✅ error 优先判断并显式报错
- ❌ error 态与 empty 态同屏并存（Alert"加载失败" + 表格"暂无数据/创建"）（F-004/022/028）→ ✅ error 必须抑制 empty 内容
- ❌ error 态无重试 / 无返回 / 无图标，用户陷入死胡同（F-005/014/021/027）→ ✅ 必带恢复路径
- ❌ loading 整页塌缩为孤立居中 Spinner，加载完成时布局跳变（F-050/025）→ ✅ List 用 Table `loading`、Detail 用骨架内 Spinner
- ❌ empty 态仅有文案、缺主操作 CTA（F-041/033）→ ✅ empty 提供"创建第一个 X"引导

### 0.3 关键导入

```typescript
// 详情页 / 多 query 子资源错误态统一组件
import { PageLayout, InlineErrorState } from '@shared/components';
// 列表页错误态（内联 Alert 范式）
import { Alert, Button } from '@cloudscape-design/components';
```

---

## 1. 错误态（最高优先级）

> 基线审计中 error 态是缺陷重灾区。本章为四态中**强制性最高**的一章。

### 1.1 四条铁律 🔴

| # | 铁律 | 反面案例 |
|---|------|---------|
| **R1** | **保留页面骨架**：error 时必须保留 `PageLayout`（标题/面包屑/操作区/筛选区），禁止 early-return 裸 `Container` | F-007/011/014/023/025 |
| **R2** | **绝不静默降级为空**：加载失败不得渲染成"0"、空数组、空表格或全绿状态 | F-001/006/024/030 |
| **R3** | **error 必抑制 empty**：错误态与空态不得同屏；失败时不提供"创建"等正向 CTA | F-004/022/028 |
| **R4** | **必带恢复路径**：error 必须提供重试（`refetch`）或返回出口，附错误图标（Cloudscape `Alert` 自带） | F-005/014/021/027 |

### 1.2 两种错误呈现范式（如实区分，不强行统一）

> ⚠️ 项目现存两种 error 呈现方式，**各有适用场景**，生成代码时按页面类型选择，不要互相替换：

| 范式 | 适用场景 | 实现 | 现有范例 |
|------|---------|------|---------|
| **A. `InlineErrorState`** | 详情页主资源失败、多 query 子资源失败 | `@shared/components` 的 `InlineErrorState`（`Alert type="error"` + 重试封装） | `TrainingJobDetailPage`、`ModelVersionsPage` |
| **B. 内联 `Alert`** | 列表页主查询失败（需保留过滤器与表格外壳） | `PageLayout` 内 `SpaceBetween` 顶部直接放 `<Alert type="error">` + 重试 `Button` | `TrainingJobListPage` |

**`InlineErrorState` props**（与实现一致）:

| prop | 类型 | 说明 |
|------|------|------|
| `message?` | `string` | 错误描述，通常传 `error?.message`；缺省回退"发生未知错误,请稍后重试。" |
| `title?` | `string` | 错误标题，默认 `'加载失败'`；资源不存在时可传 `'任务不存在'` 等 |
| `onRetry?` | `() => void` | 提供时渲染"重试"按钮，通常传 query 的 `refetch`；纯"不存在"场景可不传 |

### 1.3 代码骨架

**骨架 1 — 详情页主资源错误（范式 A）**

```tsx
import { PageLayout, InlineErrorState } from '@shared/components';

const { data: job, isLoading, error, refetch } = useTrainingJob(jobId);

// error 或 data 为空都进入错误态：保留固定标题 + 面包屑（R1）
if (error || !job) {
  return (
    <PageLayout title="训练任务详情" breadcrumbs={breadcrumbs}>
      <InlineErrorState
        title={error ? '加载失败' : '任务不存在'}
        message={error?.message ?? '未找到该训练任务，它可能已被删除。'}
        onRetry={error ? () => refetch() : undefined}  // 不存在场景不给重试（R4）
      />
    </PageLayout>
  );
}
```

**骨架 2 — 列表页错误（范式 B）**

```tsx
import { Alert, Button, SpaceBetween } from '@cloudscape-design/components';
import { PageLayout } from '@shared/components';

const { data, isLoading, error, refetch } = useTrainingJobs(queryFilters, 30000);

return (
  <PageLayout title="训练任务管理" breadcrumbs={BREADCRUMBS} actions={/* ... */}>
    <SpaceBetween size="l">
      {/* error 置于骨架内顶部，保留过滤器与重试入口（R1/R4） */}
      {error && (
        <Alert
          type="error"
          header="加载失败"
          action={<Button onClick={() => refetch()}>重试</Button>}
        >
          {error.message}
        </Alert>
      )}

      {/* 过滤器 + 表格照常渲染骨架；下方 Table 的 empty 槽由 loading 抑制 */}
      <TrainingJobTable items={data?.items ?? []} loading={isLoading} /* ... */ />
    </SpaceBetween>
  </PageLayout>
);
```

**骨架 3 — 多 query 页面子资源错误（范式 A，显式报错不降级）**

```tsx
// 主资源（model）与子资源（versions）各自独立 query
const { data: model, isLoading: modelLoading } = useModel(modelId);
const { data: versionsData, isLoading: versionsLoading, isError: versionsError, refetch } =
  useModelVersions(modelId);

// 主资源不存在 → 保留骨架报错
if (!model) {
  return (
    <PageLayout title="模型版本历史" breadcrumbs={breadcrumbs}>
      <InlineErrorState title="模型不存在" message="未找到该模型，无法查看版本历史。" />
    </PageLayout>
  );
}

return (
  <PageLayout title={`${model.model_name} - 版本历史`} breadcrumbs={breadcrumbs} actions={/* ... */}>
    <SpaceBetween size="l">
      {/* 子资源加载失败：显式报错，绝不静默降级为空表（R2/F-006） */}
      {versionsError && (
        <InlineErrorState message="版本列表加载失败。" onRetry={() => refetch()} />
      )}

      <ModelVersionTable versions={versionsData?.versions ?? []} loading={versionsLoading} /* ... */ />
    </SpaceBetween>
  </PageLayout>
);
```

### 1.4 反模式对照

| ❌ 反模式 | ✅ 正确做法 | 关联 |
|----------|-----------|------|
| `if (error) return <Container>加载失败</Container>` | `PageLayout` 骨架内 `InlineErrorState` / `Alert` | R1 / F-007 |
| `if (error) return <Box>{error.message}</Box>`（裸红字，无图标/重试） | Cloudscape `Alert type="error"` + 重试 `Button` | R4 / F-021/027 |
| `items={data?.items ?? []}` 但**不判断 error** → 失败显示空表 | 先 `{error && <InlineErrorState .../>}` 再渲染表格 | R2 / F-006 |
| 指标 `value={data?.count ?? 0}`、状态固定"运行正常" | 失败时整体降级为错误提示 / "未知" | R2 / F-001/030 |
| error `Alert` 与 Table `empty`"创建第一个"同屏 | error 时 Table 由 `loading`/数据为空但无 empty CTA 抑制，或仅显示中性"暂无" | R3 / F-004/028 |

### 1.5 错误文案措辞

错误标题/正文的具体措辞（"加载失败" vs "任务不存在"、是否含操作建议、语气）遵循 → [ux-writing.md](ux-writing.md)。本规范只约束**结构与呈现**，不重复定义文案细则。

---

## 2. 加载态

### 2.1 骨架屏 vs Spinner 决策

| 页面类型 | 加载呈现 | 理由 |
|---------|---------|------|
| List 列表页 | Table `loading={isLoading}` + `loadingText` | Table 自带骨架行，保留表头与外壳，无布局跳变 |
| Detail 详情页 | `PageLayout` 骨架内 `<Spinner size="large">` + "加载中..." | 保留页面 chrome；首屏 query 未返回前可临时整页 Spinner，但**标题应尽量稳定**（见 §2.3） |
| Tab/子区块 | 区块内 `<Spinner>` + 文案 | 局部加载不阻塞已渲染区块（如日志 Tab 单独 loading） |
| Dashboard | 各指标卡 / 图表骨架占位 | ❌ 禁止整页塌缩为单个孤立 Spinner（F-050），否则加载完成时布局剧烈跳变 |

### 2.2 代码骨架

```tsx
// List：交给 Table 处理，保留外壳
<TrainingJobTable items={data?.items ?? []} loading={isLoading} totalCount={data?.total} />

// Detail：骨架内 Spinner（Cloudscape 居中模式）
if (isLoading) {
  return (
    <Box textAlign="center" padding="xxl">
      <Spinner size="large" />
      <Box margin={{ top: 'm' }}>加载中...</Box>
    </Box>
  );
}
```

### 2.3 陷阱 ⚠️

- ❌ 整页 `loading` 时只剩居中 Spinner，加载完出现完整布局 → 视觉跳变（F-050）→ ✅ 复杂页用骨架占位
- ❌ loading 态标题用泛化"空间详情"，default 态变实体名"running-jupyter-space" → 标题跳变（F-029）→ ✅ 标题尽量保持稳定，或加载前用通用标题、加载后平滑替换
- ❌ 加载范围不一致：表格显示"加载中"但旁边卡片区已满载静态数据（F-026）→ ✅ 同一数据源的区块统一进入 loading

---

## 3. 空态

### 3.1 空态规则

| 规则 | 说明 |
|------|------|
| **empty ≠ error** | "无数据"与"加载失败"是两种语义，必须用不同呈现区分（F-006/024）。error 优先于 empty 判断 |
| **empty 必带引导 CTA** | List/集合空态应提供主操作（如"注册第一个数据集""创建第一个版本"），引导用户起步 |
| **empty 文案中性** | 空态文案描述"暂无 X"，不暗示故障 |

> ⚠️ 待改项：部分页面空态缺 CTA（F-041 dataset-list；F-033 admin-home dashboard 空列表缺"新建用户"）。新页面必须补齐，存量页面在阶段 4 修复。

### 3.2 代码骨架

```tsx
// Table empty 槽：中性文案 + 主操作 CTA
<Table
  items={data?.items ?? []}
  loading={isLoading}
  empty={
    <Box textAlign="center" padding="l">
      <SpaceBetween size="s">
        <Box variant="strong">暂无数据集</Box>
        <Button variant="primary" onClick={handleCreate}>注册第一个数据集</Button>
      </SpaceBetween>
    </Box>
  }
  columnDefinitions={[/* ... */]}
/>

// 子区块空态：仅中性文案即可（无需 CTA）
empty={<Box textAlign="center" color="inherit" padding="l">暂无检查点</Box>}
```

### 3.3 空态文案

空态主文案与 CTA 措辞遵循 → [ux-writing.md](ux-writing.md)。

---

## 4. 成功态

### 4.1 mutation 成功反馈

| 操作 | 反馈 | 跳转 |
|------|------|------|
| 创建实体 | `Flashbar` success（"任务创建成功"） | 跳转列表或新建详情页 |
| 删除实体 | `Flashbar` success | 留在列表（已自动失效刷新） |
| 暂停/恢复/回滚等状态变更 | `Flashbar` success + `refetch()` 刷新当前视图 | 留在原页 |

> Flashbar 通过 `@shared/events` EventBus 的 `notification:show` 统一驱动（详见 [state-management.md](state-management.md) §4）；mutation `onSuccess` 中触发反馈 + Query 失效。

### 4.2 代码骨架

```tsx
// mutation onSuccess：发布成功通知 + 失效缓存（驱动列表刷新）
export function useCreateTrainingJob() {
  const queryClient = useQueryClient();
  const publish = useEventPublisher();
  return useMutation({
    mutationFn: createTrainingJob,
    onSuccess: (job) => {
      publish('notification:show', { type: 'success', message: '任务创建成功' });
      queryClient.invalidateQueries({ queryKey: queryKeys.trainingJobs.lists() });
    },
  });
}

// 页面侧：成功后跳转
const handleDelete = useCallback(async () => {
  await deleteMutation.mutateAsync(jobId);
  setShowDeleteModal(false);
  navigate('/training-jobs');
}, [jobId, deleteMutation, navigate]);
```

> Flashbar / Modal 二次确认等交互细则详见 [component-design.md](component-design.md) §4。

---

## 5. 状态完整性矩阵

> 每个页面类型 × 四态应渲染什么。生成页面时逐格对照，确保无遗漏。

| 页面类型 | default | loading | empty | error |
|---------|---------|---------|-------|-------|
| **List 列表页** | `Table` 渲染 `items`；Header 带 `counter`；过滤器/分页可用 | `Table loading` + `loadingText`；外壳（标题/面包屑/过滤器）保留 | `Table empty` 槽：中性文案 + **主操作 CTA** | 顶部内联 `Alert type="error"` + 重试；过滤器与表格外壳保留；**抑制 empty CTA** |
| **Detail 详情页** | 概览/进度/Tab 等实体区块 | `PageLayout` 骨架内 Spinner；标题稳定 | 子区块各自 empty（如"暂无检查点/日志"） | `PageLayout` 骨架内 `InlineErrorState`（固定标题 + 面包屑 + 重试/返回） |
| **Form 表单页** | 字段可编辑；必填项显式标记 | 提交时按钮 `loading` + 禁用，防重复提交 | （无 empty 态） | 字段级 `errorText`（Zod 校验）；提交失败 `Alert`/`Flashbar`，保留已填值 |
| **Dashboard 仪表盘** | 指标卡 + 图表（量纲一致） | 各区块骨架占位，避免整页 Spinner | "暂无数据"区块（中性） | **整体降级报错**（Alert/Flashbar）；指标/状态显示"未知/无法获取"，**禁止伪装为 0/空/全绿** |

---

## 已知差距清单

> 本规范定义目标范式；以下为存量页面与目标的差距，由阶段 4 修复任务按编号消化。

| 编号 | 严重度 | 差距 | 涉及页面 |
|------|:-----:|------|---------|
| F-001 | P0 | Dashboard error 静默降级为"0 + 空图表 + 全绿"，伪装健康 | dashboard/home |
| F-004 | P0 | error Alert 与 empty"创建"CTA 同屏，语义矛盾 | spaces/space-list |
| F-005 | P0 | Detail error 死胡同：无骨架/无重试/无返回 | models/model-detail |
| F-006 | P0 | 子资源 error 与 empty 渲染一致，失败降级为"无数据" | models/model-versions |
| F-007 | P0 | error 整页塌缩为裸容器，丢失骨架 | audit/audit-logs |
| F-008 | P0 | error 呈现跨模块不一致，缺统一组件 | audit/audit-logs |
| F-011 | P0 | error 丢失整页骨架，走独立渲染分支 | reports/resource-usage、cost-analysis |
| F-014 | P0 | error 整页框架塌缩，无重试/无导航出口 | admin/user-management |
| F-021 | P1 | error 裸红字，缺图标/返回/重试，与 list 不统一 | training/training-detail |
| F-022 | P1 | error 下表格叠加 empty 文案 | training/training-list |
| F-023 | P1 | loading/error 丢失 Header 与面包屑 | datasets/dataset-detail |
| F-024 | P1 | error 与 empty 视觉相同，未区分语义 | datasets/dataset-versions |
| F-025 | P1 | loading 孤立 spinner；error 纯红字非 Alert | templates/template-detail |
| F-026 | P1 | empty/loading 范围不一致（卡片满载、表格空/加载）；error 缺重试 | templates/template-list |
| F-027 | P1 | error 纯红字，无重试/图标/引导 | monitoring/monitoring |
| F-028 | P1 | error Alert 缺重试，且与 empty"暂无配置"叠加 | resource-quotas |
| F-029 | P1 | loading 标题泛化、default 实体名，标题跳变 | spaces/space-detail |
| F-030 | P1 | error 时系统状态仍显示全绿"运行正常" | dashboard/home |
| F-033 | P1 | Dashboard 空列表缺"新建用户"主操作 CTA | admin/admin-home |
| F-041 | P2 | empty 态缺引导主操作按钮（"注册第一个数据集"） | datasets/dataset-list |
| F-050 | P2 | loading 整页单 Spinner，缺骨架占位，布局跳变 | monitoring/monitoring |
