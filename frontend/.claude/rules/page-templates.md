> **职责**: 页面模板规范 - 四大页面模式骨架（List / Detail / Form / Dashboard）与图表严谨性

# 页面模板规范 (Page Templates Standards)

> **适用范围**: 所有 features 页面的区域结构与骨架——四大页面模式的必备元素、PageLayout 用法、Cloudscape 组件映射、图表量纲规则
> **事实基准**: 反向提炼自已落地的 `TrainingJobListPage` / `TrainingJobDetailPage` / `CreateTrainingJobPage` / `HomePage` 与 [`PageLayout`](../../src/shared/components/PageLayout.tsx)；图表问题依据 2026-06-13 baseline 审计 F-009/010/012/013
> **核心命题**: 同一类页面用同一套骨架。所有页面都以 `PageLayout` 为最外层容器，区域结构、必备元素、四态接入点统一；图表必须同图同量纲，禁止把百分比与绝对值、聚合值与分项混在一张图。

---

## 0. 速查卡片

> Claude 生成页面时优先查阅此章节

### 0.1 四大页面模式：何时用哪个（决策表）

| 页面模式 | 何时用 | 典型实例 | 路由形态 | 关键骨架 |
|---------|--------|---------|---------|---------|
| **List 列表页** | 展示某实体的集合，支持筛选/排序/分页/批量进入详情 | 训练任务列表、数据集列表、模型库 | `/{entity}` | PageLayout + 筛选区 + Table |
| **Detail 详情页** | 展示单个实体的完整信息 + 状态 + 子资源 + 操作 | 训练任务详情、模型详情、空间详情 | `/{entity}/:id` | PageLayout + 概览 KeyValuePairs + Tabs(子资源) + 轮询 |
| **Form 表单页** | 创建/编辑单个实体，字段校验后提交 | 创建训练任务、上传数据集 | `/{entity}/create`、`/{entity}/:id/edit` | PageLayout + Form + Container 分组 + FormField |
| **Dashboard 仪表盘** | 跨实体聚合概览：关键指标 + 图表 + 快捷入口 | 首页门户、监控总览 | `/`、`/monitoring` | PageLayout(hero) + 指标卡行 + 主图表区 + 快捷入口 |

**选择要点**:
- 「一个实体的多个属性」→ Detail；「多个实体的同类属性」→ List。
- Detail 子资源用 **Tabs**（配置/检查点/日志/指标），不要堆成超长单页。
- Form 字段 ≤ 一屏、无强顺序依赖 → 单页 `Form`；字段多、有阶段顺序 → `Wizard`（§3.2）。
- 仅门户型 / 总览型页面用 `hero` 页头（§4.2），常规 List/Detail/Form **不用** hero。

### 0.2 `PageLayout` props 速查（与 [组件实现](../../src/shared/components/PageLayout.tsx) 逐字一致）

| prop | 类型 | 说明 | 四大模式用法 |
|------|------|------|------------|
| `title` | `string` | 页面标题（必填） | 全部必填；Detail 用实体名，error 态用固定通用名（§2.3） |
| `description` | `React.ReactNode` | 标题下方描述 | List/Form/Dashboard 常用；Detail 可放实体摘要 |
| `actions` | `React.ReactNode` | 标题右侧操作区 | 多按钮用 `<SpaceBetween direction="horizontal" size="xs">` 包裹 |
| `counter` | `string` | 计数信息如 `(20)`，显示在标题右侧 | List 可传总数计数（亦可交给 Table Header 的 `counter`，§1.2） |
| `headerVariant` | `HeaderProps['variant']` | 标题层级，默认 `h1` | 一般不改，保持 `h1` |
| `hero` | `boolean` | 品牌 Hero 页头（深空渐变高对比背景） | **仅 Dashboard/门户页**置 `true`（§4.2） |
| `heroExtra` | `React.ReactNode` | hero 模式下标题区附加内容（仅 `hero` 时生效） | Dashboard 放状态摘要 `StatusIndicator` 行 |
| `breadcrumbs` | `BreadcrumbItem[]` | 面包屑，自动同步到全局 UI Store；不传则清空 | List/Detail/Form 必传；Dashboard 首页可不传 |
| `children` | `React.ReactNode` | 页面内容（必填） | 统一用 `<SpaceBetween size="l">` 组织纵向区块 |

> ⚠️ `PageLayout` **只有上述 props**。没有 `loadingText`、`error`、`empty` 等状态 props——四态由 `children` 内部按 [interaction-states.md](interaction-states.md) 处理，不是 PageLayout 的职责。

### 0.3 陷阱 ⚠️

- ❌ 页面不套 `PageLayout`，直接堆 `Container` → ✅ 所有 features 页面以 `PageLayout` 为最外层（统一页头/面包屑/间距）
- ❌ error 时 early-return 裸 `Container`，丢失标题/面包屑/筛选区 → ✅ 保留 `PageLayout` 骨架再报错（四态见 [interaction-states.md](interaction-states.md) §1）
- ❌ 把百分比指标与绝对字节数画进同一条 Y 轴 → ✅ 同图同量纲，异量纲拆图（§5.1）
- ❌ 把「总计」聚合值与各分项画进同一折线图 → ✅ 总计单独 KPI 或独立图，分项另开一图（§5.2）
- ❌ 给图表硬塞 hex 颜色数组、跨图同色不同义 → ✅ 走 design token 分类色板，跨图配色语义一致（§5.3，[design-tokens.md](design-tokens.md) §3）
- ❌ 常规列表/详情页套 `hero` → ✅ hero 仅限门户/总览（§4.2）
- ❌ children 用 `margin`/`padding` 堆间距 → ✅ `<SpaceBetween size="l">` 组织纵向区块

---

## 1. List 列表页模板

### 1.1 区域结构

```
┌─ PageLayout ─────────────────────────────────────────────┐
│  ╔═ Header (PageLayout 注入) ═══════════════════════════╗ │
│  ║  面包屑: 首页 / 训练任务                              ║ │
│  ║  H1 标题  [counter (20)]            [刷新] [＋创建]  ║ │  ← title / counter / actions
│  ║  描述文本                                            ║ │
│  ╚══════════════════════════════════════════════════════╝ │
│  ┌─ children: <SpaceBetween size="l"> ──────────────────┐ │
│  │  [error 时] Alert type="error" + 重试   ← 抑制 empty │ │
│  │  ┌─ Container（筛选区）────────────────────────────┐ │ │
│  │  │  [Select 状态] [Select 优先级] [搜索…]          │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌─ Table ──────────────────────────────────────────┐ │ │
│  │  │ Header(counter) │ 列排序 │ 列偏好 ⚙ │ 分页 ◀ ▶  │ │ │
│  │  │ ─ row ─ … （loading 骨架行 / empty 槽带 CTA）    │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 1.2 必备元素清单

| 元素 | 要求 | 落地 |
|------|------|------|
| **标题 + 计数** | H1 标题 + 集合总数 | `PageLayout title` + `counter`，或 Table 内 `<Header counter={`(${total})`}>` |
| **面包屑** | `首页 / {实体}`，模块级常量避免重建引用 | `PageLayout breadcrumbs`（常量 `BREADCRUMBS`） |
| **主操作按钮** | 右上「创建」为 `variant="primary"`；可附「刷新」 | `actions` 内 `SpaceBetween direction="horizontal"` |
| **筛选区** | 状态/优先级等过滤；改筛选回到第 1 页 | `Container` + `Select`（变更时 `setFilters(p => ({...p, page: 1}))`） |
| **Table：排序** | 可排序列声明 `sortingField`，受控 `sortingColumn` | Table `sortingColumn` / `onSortingChange` |
| **Table：分页** | 受控分页，页码与 `total_pages` 联动 | Table `pagination`（或独立 `Pagination`）+ `onPageChange` |
| **Table：列偏好** | 用户可显隐/排序列 | Table `preferences` + `<CollectionPreferences>` |
| **四态** | default/loading/empty/error 全处理 | 见 §1.4 |

> 列偏好与排序未在现有 `TrainingJobListPage` 全部接线（筛选/分页已接，列偏好待补）——新列表页应一次补齐上表全部，存量页按已知差距清单消化。

### 1.3 Cloudscape 组件映射

| 区域 | 组件 |
|------|------|
| 最外层 | `PageLayout`（封装 `ContentLayout` + `Header`） |
| 操作区 | `Button`（`variant="primary"` 主操作）+ `SpaceBetween` |
| 筛选区 | `Container` + `Select` / `Input`（搜索）/ `PropertyFilter`（复杂筛选） |
| 数据区 | `Table`（首选）或 `Cards`（卡片视图） |
| 分页 | `Table pagination` 或独立 `Pagination` |
| 列偏好 | `CollectionPreferences` |
| 错误提示 | `Alert type="error"` + 重试 `Button` |

### 1.4 四态接入点 → [interaction-states.md](interaction-states.md)

| 态 | 接入方式 |
|----|---------|
| default | Table 渲染 `items`；Header 带 `counter`；筛选/分页可用 |
| loading | Table `loading={isLoading}` + `loadingText`；外壳（标题/面包屑/筛选区）保留，**不**整页塌缩 Spinner |
| empty | Table `empty` 槽：中性文案 + **主操作 CTA**（"创建第一个 X"，文案见 [ux-writing.md](ux-writing.md) §2.1） |
| error | 顶部内联 `Alert type="error"` + 重试；筛选区与表格外壳保留；**抑制 empty CTA**（[interaction-states.md](interaction-states.md) §1 范式 B） |

### 1.5 可复制骨架

```tsx
import { Alert, Button, Container, Select, SpaceBetween } from '@cloudscape-design/components';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useTrainingJobs } from '../api';
import { TrainingJobTable } from '../components';
import type { TrainingJobFilters } from '../types';

// 面包屑：模块级常量，避免每次渲染创建新引用
const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '训练任务', href: '/training-jobs' },
];

const defaultFilters: TrainingJobFilters = { page: 1, page_size: 20 };

export function TrainingJobListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<TrainingJobFilters>(defaultFilters);

  // 列表查询（可带轮询间隔）
  const { data, isLoading, error, refetch } = useTrainingJobs(filters, 30000);

  // 改筛选回到第 1 页
  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  return (
    <PageLayout
      title="训练任务管理"
      description="提交、监控和管理分布式训练任务"
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>刷新</Button>
          <Button variant="primary" iconName="add-plus" onClick={() => navigate('/training-jobs/create')}>
            创建训练任务
          </Button>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {/* error：骨架内顶部报错，保留筛选区与重试入口（抑制 empty CTA） */}
        {error && (
          <Alert type="error" header="加载失败" action={<Button onClick={() => refetch()}>重试</Button>}>
            {error.message}
          </Alert>
        )}

        {/* 筛选区 */}
        <Container>
          <SpaceBetween direction="horizontal" size="m">
            <Select selectedOption={/* ... */ null} options={[]} placeholder="选择状态" onChange={() => {}} />
            <Select selectedOption={/* ... */ null} options={[]} placeholder="选择优先级" onChange={() => {}} />
          </SpaceBetween>
        </Container>

        {/* 数据表：loading / empty 槽由 Table 处理（empty 带 CTA） */}
        <TrainingJobTable
          items={data?.items ?? []}
          loading={isLoading}
          totalCount={data?.total}
          currentPage={filters.page ?? 1}
          totalPages={data?.total_pages ?? 1}
          onPageChange={handlePageChange}
          onJobClick={(id) => navigate(`/training-jobs/${id}`)}
        />
      </SpaceBetween>
    </PageLayout>
  );
}
```

---

## 2. Detail 详情页模板

### 2.1 区域结构

```
┌─ PageLayout ─────────────────────────────────────────────┐
│  ╔═ Header ════════════════════════════════════════════╗ │
│  ║  面包屑: 首页 / 训练任务 / {job_name}                ║ │  ← breadcrumbs (useMemo, 随实体名更新)
│  ║  H1 {job_name}        [刷新][暂停][恢复][删除]       ║ │  ← title=实体名 / actions=状态相关操作组
│  ║  描述（实体摘要）                                    ║ │
│  ╚══════════════════════════════════════════════════════╝ │
│  ┌─ children: <SpaceBetween size="l"> ──────────────────┐ │
│  │  ┌─ Container header="概览" ──────────────────────┐  │ │
│  │  │  ColumnLayout / KeyValuePairs：状态 优先级 …    │  │ │  ← StatusIndicator 显状态
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌─ Container header="训练进度"（条件区块）───────┐  │ │
│  │  │  当前 Epoch / Step / 完成度                     │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌─ Tabs（子资源）──────────────────────────────────┐ │ │
│  │  │ [配置] [检查点(n)] [日志] [训练指标]             │ │ │  ← 子资源分 Tab
│  │  │   …KeyValuePairs / Table(检查点) / 日志 / 图表…  │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌─ Modal（删除二次确认，按需）─────────────────────┐ │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
   ↻ 轮询：running 状态时按间隔（如日志 5s）自动刷新
```

### 2.2 必备元素清单

| 元素 | 要求 | 落地 |
|------|------|------|
| **面包屑（动态）** | `首页 / {实体} / {实体名}`，实体名加载后更新 | `useMemo(() => [...], [entity?.name])` → `PageLayout breadcrumbs` |
| **标题 = 实体名** | H1 用实体名（如 `job.job_name`） | `PageLayout title={job.job_name}` |
| **操作组（状态驱动）** | 操作按钮按状态启用/禁用（如运行中可暂停、非运行可删除） | `actions` 内 `SpaceBetween direction="horizontal"`；`canPause`/`canResume`/`canDelete` 派生自 `status` |
| **概览区** | 关键属性一览（状态/优先级/策略/时长） | `Container header="概览"` + `ColumnLayout variant="text-grid"` 或 `KeyValuePairs` |
| **子资源 Tabs** | 配置/检查点/日志/指标分 Tab，不堆超长单页 | `<Tabs tabs={[...]}>`；子表用 `Table variant="embedded"` |
| **状态展示** | 颜色+图标+文字 | `<StatusIndicator>` / 状态 Badge（见 [accessibility.md](accessibility.md) §5） |
| **轮询** | 运行态自动刷新进度/日志 | query 传轮询间隔（`isRunning ? 5000 : undefined`） |
| **危险操作确认** | 删除等需二次确认 | `Modal`（文案见 [ux-writing.md](ux-writing.md) §2.3） |
| **四态** | 尤其 error 态保留骨架 | 见 §2.4 |

### 2.3 Cloudscape 组件映射

| 区域 | 组件 |
|------|------|
| 最外层 | `PageLayout` |
| 操作组 | `Button` + `SpaceBetween`（按状态控制 `disabled` / 条件渲染） |
| 概览区 | `Container` + `Header variant="h2"` + `ColumnLayout` / `KeyValuePairs` |
| 状态 | `StatusIndicator` / `Badge` |
| 子资源容器 | `Tabs` |
| 子资源表 | `Table variant="embedded"` |
| 二次确认 | `Modal` |
| 错误态 | `InlineErrorState`（`@shared/components`） |

### 2.4 四态接入点 → [interaction-states.md](interaction-states.md)

| 态 | 接入方式 |
|----|---------|
| default | 概览 + 进度 + Tabs 区块渲染 |
| loading | 首屏未返回时 `Box textAlign="center" padding="xxl"` 内 `<Spinner size="large">` + "加载中..."；标题尽量稳定（[interaction-states.md](interaction-states.md) §2.2） |
| empty | 子区块各自空文案（如"暂无检查点""暂无日志数据"，中性、无需 CTA） |
| **error**（铁律） | **保留 `PageLayout` 骨架**（固定标题 + 面包屑），内放 `InlineErrorState`：`title` 区分"加载失败"/"任务不存在"，`onRetry` 失败时给重试、纯不存在时不给（[interaction-states.md](interaction-states.md) §1 范式 A） |

**error 态固定标题骨架（必背）**:

```tsx
import { PageLayout, InlineErrorState } from '@shared/components';

const { data: job, isLoading, error, refetch } = useTrainingJob(jobId);

// error 或实体为空都进入错误态：保留固定通用标题 + 面包屑，绝不裸容器塌缩
if (error || !job) {
  return (
    <PageLayout title="训练任务详情" breadcrumbs={breadcrumbs}>
      <InlineErrorState
        title={error ? '加载失败' : '任务不存在'}
        message={error?.message ?? '未找到该训练任务，它可能已被删除。'}
        onRetry={error ? () => refetch() : undefined}
      />
    </PageLayout>
  );
}
```

### 2.5 可复制骨架

```tsx
import { Box, Button, ColumnLayout, Container, Header, KeyValuePairs, SpaceBetween, Spinner, Tabs } from '@cloudscape-design/components';
import { useMemo, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageLayout, InlineErrorState } from '@shared/components';
import { useTrainingJob, usePauseTrainingJob } from '../api';
import { TrainingStatusBadge } from '../components';

export function TrainingJobDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const jobId = id ? parseInt(id, 10) : undefined;

  const { data: job, isLoading, error, refetch } = useTrainingJob(jobId);

  // 面包屑随实体名更新（useMemo 稳定引用）
  const breadcrumbs = useMemo(
    () => [
      { text: '首页', href: '/' },
      { text: '训练任务', href: '/training-jobs' },
      { text: job?.job_name ?? '任务详情', href: '#' },
    ],
    [job?.job_name],
  );

  // 操作可用性派生自状态
  const canPause = job?.status === 'running';
  const pauseMutation = usePauseTrainingJob();
  const handlePause = useCallback(async () => {
    if (!jobId) return;
    await pauseMutation.mutateAsync(jobId);
    refetch();
  }, [jobId, pauseMutation, refetch]);

  // loading：整页居中 Spinner（首屏未返回前）
  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: 'm' }}>加载中...</Box>
      </Box>
    );
  }

  // error：保留 PageLayout 骨架 + InlineErrorState（固定标题 + 面包屑 + 重试/返回）
  if (error || !job) {
    return (
      <PageLayout title="训练任务详情" breadcrumbs={breadcrumbs}>
        <InlineErrorState
          title={error ? '加载失败' : '任务不存在'}
          message={error?.message ?? '未找到该训练任务，它可能已被删除。'}
          onRetry={error ? () => refetch() : undefined}
        />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={job.job_name}
      description={job.description || '训练任务详情、进度与运行日志'}
      breadcrumbs={breadcrumbs}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => refetch()}>刷新</Button>
          {canPause && <Button onClick={handlePause} loading={pauseMutation.isPending}>暂停</Button>}
        </SpaceBetween>
      }
    >
      <SpaceBetween size="l">
        {/* 概览区 */}
        <Container header={<Header variant="h2">概览</Header>}>
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">状态</Box>
              <TrainingStatusBadge status={job.status} />
            </div>
            {/* …其余概览字段 */}
          </ColumnLayout>
        </Container>

        {/* 子资源 Tabs */}
        <Tabs
          tabs={[
            { id: 'config', label: '配置信息', content: <Container><KeyValuePairs columns={2} items={[/* … */]} /></Container> },
            { id: 'checkpoints', label: '检查点 (0)', content: <Box padding="l">暂无检查点</Box> },
            { id: 'logs', label: '日志', content: <Box padding="l">暂无日志数据</Box> },
            { id: 'metrics', label: '训练指标', content: <Box padding="l">指标图表区（量纲规范见 §5）</Box> },
          ]}
        />
      </SpaceBetween>
    </PageLayout>
  );
}
```

---

## 3. Form 表单页模板

### 3.1 区域结构（单页 Form）

```
┌─ PageLayout ─────────────────────────────────────────────┐
│  ╔═ Header ════════════════════════════════════════════╗ │
│  ║  面包屑: 首页 / 训练任务 / 创建训练任务              ║ │  ← breadcrumbs
│  ║  H1 创建训练任务                                     ║ │  ← title
│  ║  描述：配置并提交 … 分布式训练任务                   ║ │
│  ╚══════════════════════════════════════════════════════╝ │
│  ┌─ children: <SpaceBetween size="l"> ──────────────────┐ │
│  │  [提交失败时] Alert type="error"（保留已填值）        │ │
│  │  ┌─ Form ───────────────────────────────────────────┐ │ │
│  │  │  actions=[取消] [提交]（提交时 loading + 禁用）   │ │ │
│  │  │  ┌─ Container header="基础信息" ────────────────┐ │ │ │
│  │  │  │  FormField(label/description/constraintText) │ │ │ │
│  │  │  │    + Input / Select…（errorText 字段级校验） │ │ │ │
│  │  │  └────────────────────────────────────────────────┘ │ │ │
│  │  │  ┌─ Container header="资源配置" ────────────────┐ │ │ │
│  │  │  │  …更多分组…                                  │ │ │ │
│  │  │  └────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 3.2 单页 `Form` vs 多步 `Wizard` 选择标准

| 维度 | 单页 `Form` ✅ | 多步 `Wizard` ✅ |
|------|---------------|-----------------|
| 字段数量 | 少~中（一两屏内可填完） | 多（需分阶段，避免一屏过载） |
| 字段依赖 | 无强顺序，可任意次序填写 | 有阶段顺序（前一步决定后一步选项） |
| 校验时机 | 提交时整体校验 + 字段级实时 | 每步完成校验后才能进入下一步 |
| 心智负担 | 用户一眼看全 | 拆解复杂流程，逐步引导 |
| 典型场景 | 创建任务、编辑配置 | 多阶段引导（数据源→参数→资源→确认） |

> 现有 `CreateTrainingJobPage` 用单页 `Form`（字段经 `TrainingJobForm` 内部按 `Container` 分组）。字段超过一屏、出现阶段依赖时再升级为 `Wizard`。

### 3.3 必备元素清单

| 元素 | 要求 | 落地 |
|------|------|------|
| **标题 + 面包屑** | 「创建{实体}」/「编辑{实体}」 | `PageLayout title` + `breadcrumbs` |
| **Form 容器** | 提交/取消按钮置于 `Form actions` | `<Form actions={<SpaceBetween direction="horizontal">…}>` |
| **Container 分组** | 字段按语义分块（基础/资源/高级） | 每组一个 `Container header={<Header variant="h2">…}` |
| **FormField 校验** | label + description + constraintText 分工 | `FormField`（`description` 说语义、`constraintText` 说约束，见 [ux-writing.md](ux-writing.md) §2.4） |
| **必填标记** | 必填字段显式标注 | `FormField` constraintText 标"必填" |
| **字段级错误** | 校验失败就近提示 | `FormField errorText`（Zod message，见 [state-management.md](state-management.md) §3） |
| **提交反馈** | 提交时按钮 loading + 禁用防重复 | 主按钮 `loading={isSubmitting}` |
| **四态** | 表单无 empty 态；重点 error | 见 §3.5 |

### 3.4 Cloudscape 组件映射

| 区域 | 组件 |
|------|------|
| 最外层 | `PageLayout` |
| 表单容器 | `Form`（`actions` 槽放提交/取消） |
| 字段分组 | `Container` + `Header variant="h2"` |
| 字段 | `FormField` + `Input` / `Select` / `Multiselect` / `Textarea` / `Toggle` 等 |
| 多步流程 | `Wizard`（替代 `Form`，见 §3.2） |
| 提交失败 | `Alert type="error"` / `Flashbar` |

### 3.5 四态接入点 + 成功反馈链路 → [interaction-states.md](interaction-states.md)

| 态 | 接入方式 |
|----|---------|
| default | 字段可编辑；必填项显式标记 |
| loading | 提交时主按钮 `loading` + 禁用，防重复提交 |
| empty | 表单无 empty 态 |
| error | 字段级 `errorText`（Zod 校验）；提交失败顶部 `Alert`/`Flashbar`，**保留已填值** |

**提交成功链路**（→ [interaction-states.md](interaction-states.md) §4 成功态）:

```tsx
const handleSubmit = useCallback(async (data: CreateTrainingJobRequest) => {
  try {
    const result = await createMutation.mutateAsync(data);
    // mutation onSuccess 发布 notification:show（success）+ 失效列表缓存
    navigate(`/training-jobs/${result.id}`); // 创建成功 → 跳转新建详情页
  } catch (error) {
    console.error('创建训练任务失败:', error); // 错误由 mutation onError → Alert/Flashbar 呈现
  }
}, [createMutation, navigate]);
```

### 3.6 可复制骨架

```tsx
import { Alert, SpaceBetween } from '@cloudscape-design/components';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '@shared/components';
import { useCreateTrainingJob } from '../api';
import { TrainingJobForm } from '../components/TrainingJobForm';
import type { CreateTrainingJobRequest } from '../types';

const BREADCRUMBS = [
  { text: '首页', href: '/' },
  { text: '训练任务', href: '/training-jobs' },
  { text: '创建训练任务', href: '#' },
];

export function CreateTrainingJobPage() {
  const navigate = useNavigate();
  const createMutation = useCreateTrainingJob();

  const handleSubmit = useCallback(async (data: CreateTrainingJobRequest) => {
    try {
      const result = await createMutation.mutateAsync(data);
      navigate(`/training-jobs/${result.id}`); // 成功 → 跳详情
    } catch (error) {
      console.error('创建训练任务失败:', error); // 失败 → 下方 Alert 呈现
    }
  }, [createMutation, navigate]);

  return (
    <PageLayout
      title="创建训练任务"
      description="配置并提交 DDP / FSDP / DeepSpeed 分布式训练任务"
      breadcrumbs={BREADCRUMBS}
    >
      <SpaceBetween size="l">
        {/* 提交失败：顶部 Alert，保留已填值 */}
        {createMutation.isError && (
          <Alert type="error" header="创建失败">
            {createMutation.error?.message || '未知错误'}
          </Alert>
        )}

        {/* 表单组件内部：Form + Container 分组 + FormField 校验，主按钮 loading=isSubmitting */}
        <TrainingJobForm
          onSubmit={handleSubmit}
          onCancel={() => navigate('/training-jobs')}
          isSubmitting={createMutation.isPending}
        />
      </SpaceBetween>
    </PageLayout>
  );
}
```

---

## 4. Dashboard 仪表盘模板

### 4.1 区域结构（hero 门户型）

```
┌─ PageLayout hero ────────────────────────────────────────┐
│  ╔═ Header（高对比 + 深空渐变背景，§4.2）═══════════════╗ │
│  ║  H1 早上好，{用户名}                  [＋创建任务]   ║ │  ← title / actions
│  ║  描述：AI 训练平台运行状态与关键指标一览            ║ │
│  ║  heroExtra: ● 平台服务运行正常   ● 3 个任务训练中   ║ │  ← heroExtra: StatusIndicator 行
│  ╚══════════════════════════════════════════════════════╝ │
│  ┌─ children: <SpaceBetween size="l"> ──────────────────┐ │
│  │  [error 时] InlineErrorState（整体降级，不伪装健康） │ │
│  │  ┌─ 指标卡行：ColumnLayout columns={4} ─────────────┐ │ │
│  │  │ [▣ 任务总数] [▣ 运行中] [▣ 数据集] [▣ 模型]      │ │ │  ← MetricCard：图标+大数字
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌─ 主图表区：ColumnLayout columns={2} ─────────────┐ │ │
│  │  │ ┌ Container 状态分布 ┐ ┌ Container 系统状态 ┐    │ │ │  ← PieChart / StatusIndicator
│  │  │ │   PieChart(donut)  │ │   关键状态网格      │    │ │ │
│  │  │ └────────────────────┘ └─────────────────────┘    │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌─ 快捷入口：Container + Cards ────────────────────┐ │ │
│  │  │ [创建任务→] [上传数据集→] [开发空间→] [监控→]    │ │ │  ← 常用工作流直达
│  │  └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 4.2 `hero` / `heroExtra` 用法

| prop | 用法 | 现有范例 |
|------|------|---------|
| `hero={true}` | 开启深空渐变高对比页头（[design-tokens.md](design-tokens.md) §5.1），**仅门户/总览页** | `HomePage` |
| `heroExtra` | 标题区下方附加内容，放平台状态摘要 `StatusIndicator` 行（`SpaceBetween direction="horizontal"`） | `HomePage`：服务状态 + 运行任务数 |

> `heroExtra` 仅在 `hero` 为真时渲染（见 [PageLayout 实现](../../src/shared/components/PageLayout.tsx)）。常规 List/Detail/Form **不传** `hero`，保持默认页头。

### 4.3 必备元素清单

| 元素 | 要求 | 落地 |
|------|------|------|
| **指标卡行** | 关键计数，图标 + 大数字（`display-l`），可点击下钻 | `ColumnLayout columns={4}` + 自定义 `MetricCard`（`Container` + `Icon` + `Box fontSize="display-l"` + `Link`） |
| **主图表区** | 状态分布 / 资源趋势等，**量纲必须一致（§5）** | `ColumnLayout columns={2}` + `Container` + Cloudscape 图表 |
| **快捷入口** | 常用工作流直达卡片 | `Container` + `Cards`（每卡 `Link` + `Button` 前往） |
| **hero 页头** | 门户型品牌页头 + 状态摘要 | `PageLayout hero heroExtra={…}` |
| **四态** | 关键：error 整体降级，禁止伪装健康 | 见 §4.4 |

### 4.4 四态接入点 → [interaction-states.md](interaction-states.md)

| 态 | 接入方式 |
|----|---------|
| default | 指标卡 + 图表（量纲一致）+ 快捷入口 |
| loading | 各区块骨架占位（指标卡显 `—`、图表 `statusType="loading"`）；**禁止整页塌缩为孤立 Spinner**（F-050） |
| empty | "暂无数据"区块（中性）；图表 `empty` 槽 |
| **error**（铁律） | **整体降级报错**（`InlineErrorState`/`Alert`），指标/状态显示"未知/无法获取"；**禁止把失败伪装成"0 + 空图表 + 全绿"**（F-001/030，[interaction-states.md](interaction-states.md) §1 R2） |

### 4.5 Cloudscape 组件映射

| 区域 | 组件 |
|------|------|
| 最外层 | `PageLayout hero heroExtra` |
| 指标卡 | `ColumnLayout` + `Container fitHeight` + `Icon` + `Box fontSize="display-l"` + `Link` |
| 状态摘要 | `StatusIndicator`（`heroExtra` 内） |
| 图表 | `PieChart` / `BarChart` / `LineChart` / `AreaChart`（**Cloudscape 内置，见 §5**） |
| 快捷入口 | `Cards` + `Link` + `Button` |
| 错误态 | `InlineErrorState` |

---

## 5. 图表严谨性规范（Top 5）

> 图表是 Dashboard / 详情页指标 Tab 的核心。baseline 审计中量纲混用导致多张图退化为不可读（F-009/010/012/013）。本章为图表的**强制规则**。

### 5.1 同图同量纲 🔴

**一张图的同一条坐标轴上，所有数据系列必须是同一量纲（同一单位、同一数量级）。**

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| 百分比指标（CPU 62% / 内存 48% / GPU 87%）与存储**绝对字节数**（50 万级）共用一条 Y 轴 → 百分比柱被压成贴地细线，整图退化为"单根存储柱"（F-009） | 百分比一张图（0–100% 轴），绝对值另一张图（字节轴），或用双轴/分面分别承载 |
| 个位数指标与百万级指标同轴 | 量级悬殊的系列拆图，或对数轴（标注清楚） |

**规则**: 量纲（单位）不同或数量级悬殊（>2 个数量级）的系列，**不得共用一条坐标轴**——拆成多张图或多个子图。

### 5.2 聚合值与分项分离 🔴

**「总计」聚合值不得与其各分项画在同一张折线/柱状图。**

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| 成本「总计」与计算/存储/网络/其他**分项**同一折线图 → 总计与最大分项两条线高度重叠不可区分，小分项被压贴底不可读（F-012） | 总计单独做一个 **KPI 数字**（`Box fontSize="display-l"`）或**独立趋势图**；各分项另开一张图（堆叠面积/分组柱） |
| 总量 + 构成混在一图 | 总量用 KPI / 环形图内心值；构成用堆叠图或独立分类图 |

**规则**: 总计 = KPI 或独立图；分项 = 另一张图。`PieChart` 的 `innerMetricValue` 适合放"总计"，扇区放分项占比（如 `HomePage` 任务总数置于 donut 内心）。

### 5.3 类别配色用 design token 分类色序列 🔴

**多类别图表的颜色必须取自 [design-tokens.md](design-tokens.md) §3 的分类色板，且跨图同一语义同一颜色。**

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| 给图表硬塞 hex 颜色数组 | Cloudscape 图表自动取 `colorChartsPaletteCategorical1~5`（品牌青打头），无需传 hex |
| 同色不同义：蓝色在折线图=总计、在环形图=计算（F-013） | 同一实体/类别跨所有图用**同一颜色** |
| 同义不同色："其他"折线图为灰、环形图为橙红（F-013） | 同一语义在所有图保持一致色 |
| 用分类色板表达状态语义 | 状态语义走 `JOB_STATUS_CHART_COLORS`（运行中=活跃青/完成=绿/失败=红/暂停=灰），与分类色板分离 |

**规则**: 类别区分 → `colorChartsPaletteCategorical*`（token，自动注入）；状态语义 → `JOB_STATUS_CHART_COLORS`；二者不混用。同一数据语义在跨图时颜色必须一致。文字标签走 `{ENTITY}_STATUS_LABELS`（[ux-writing.md](ux-writing.md) §1）。

### 5.4 图表组件映射

| 数据形态 | Cloudscape 组件 | 量纲注意 |
|---------|----------------|---------|
| 占比 / 构成 | `PieChart`（`variant="donut"` 可放内心总计） | 各扇区须同量纲；总计放 `innerMetricValue` |
| 分类对比 | `BarChart`（分组/堆叠） | 同轴同量纲（§5.1）；堆叠仅用于同单位可累加项 |
| 时间趋势 | `LineChart` / `AreaChart` | 总计与分项分图（§5.2）；多线同量纲 |
| 单一关键值 | `Box fontSize="display-l"`（KPI，非图表） | 总计/单指标优先用 KPI 而非塞进对比图 |

> Cloudscape 图表组件自带 loading / empty / error 状态槽（`statusType`、`empty`、`errorText`），四态接入见 [interaction-states.md](interaction-states.md)；图表配色 token 见 [design-tokens.md](design-tokens.md) §3。**禁止引入 recharts 等第三方图表库**（[tech-stack.md](tech-stack.md) 禁用清单）。

### 5.5 待改项（量纲混用）

| 编号 | 页面 | 问题 | 修复方向 |
|------|------|------|---------|
| **F-009** | monitoring/monitoring | 「资源使用对比」堆叠柱：百分比指标与存储绝对值共用 0–600000 单轴，前三组柱贴地不可见 | 百分比与字节拆为两张图（§5.1） |
| **F-010** | monitoring/monitoring | 「资源分布」环形图：CPU/内存/GPU 百分比与存储绝对值同维求占比，存储独占 95%+ 面积 | 占比图只放同量纲项；异量纲不进同一环（§5.1） |
| **F-012** | reports/cost-analysis | 成本趋势折线：「总计」与计算/存储/网络/其他分项同图，总计与计算重叠、小项贴底 | 总计转 KPI / 独立图，分项另开堆叠图（§5.2） |
| **F-013** | reports/cost-analysis | 折线图与环形图配色语义冲突（蓝色同色不同义、"其他"同义不同色） | 跨图同语义同色，走分类色 token（§5.3） |

---

## 已知差距清单

> 本规范定义目标范式；以下为存量页面与目标的差距，由阶段 4 修复任务按编号消化。

| 编号 | 维度 | 差距 | 涉及页面 |
|------|------|------|---------|
| F-009 | 图表量纲 | 「资源使用对比」堆叠柱量纲混用：百分比指标与存储绝对值共用单一 Y 轴，前三组柱贴地不可见 → 按量纲拆图（§5.1） | monitoring/monitoring |
| F-010 | 图表量纲 | 「资源分布」环形图量纲混用：三个百分比与存储绝对值同维求占比，存储独占整环 95%+，占比失真 → 异量纲不进同一环（§5.1） | monitoring/monitoring |
| F-012 | 图表聚合 | 成本趋势折线把「总计」聚合值与各分项画同图，总计与计算重叠、小项贴底不可读 → 总计转 KPI/独立图（§5.2） | reports/cost-analysis |
| F-013 | 图表配色 | 折线图与环形图颜色语义冲突（同色不同义 / 同义不同色），跨图阅读误导 → 跨图同语义同色，走分类色 token（§5.3） | reports/cost-analysis |
