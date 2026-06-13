# 阶段4：error 态统一铺开（剩余 7 个 P0 页面）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已验证的 `InlineErrorState` 组件应用到基线审计剩余的 7 个 P0 error 态页面，消除"裸 Container 塌缩"和"error 降级为空"两类缺陷。

**Architecture:** 沿用批次 0 确立的模式——error 态在 PageLayout 骨架内渲染 InlineErrorState（保留标题/面包屑 + 重试），替代 early-return 裸 Container。按改造模式分 4 个任务。全程 TDD。

**Tech Stack:** React 18 + TypeScript + Cloudscape + Vitest + Testing Library

**依据:** `frontend/docs/audit/2026-06-13-baseline/findings.md`（F-005/006/007/008/011/014）+ 批次 0 已建的 `InlineErrorState`（`@shared/components`）

---

## 背景知识（执行者必读）

**项目约定**：注释/commit 用中文；commit 格式 `<类型>(<范围>): <描述>`，范围 `frontend`。TDD 强制。Cloudscape-First。页面测试用 `vi.mock('@features/<module>/api')` 模式（**不用 MSW**），渲染用 `renderWithProviders`（`@tests/__utils__/test-utils`）。

**InlineErrorState 接口**（批次 0 已建，从 `@shared/components` 导入）：
```tsx
<InlineErrorState message?={string} title?={string} onRetry?={() => void} />
// 默认 title="加载失败"；提供 onRetry 才渲染"重试"按钮
```

**统一改造范式**（参照批次 0 已改的 `TrainingJobDetailPage.tsx`）：
裸 `if (error) return <Container><Box color="text-status-error">...</Box></Container>` →
```tsx
if (error) {
  return (
    <PageLayout title="<页面标题>" breadcrumbs={<该页 breadcrumbs>}>
      <InlineErrorState message={error.message} onRetry={() => refetch()} />
    </PageLayout>
  );
}
```

**7 个页面的精确现状（已逐个勘察，行号为勘察时点，执行时以实际为准）**：

| 页面 | 文件 | error 块行 | 现状 | refetch 解构 | 标题 / breadcrumbs |
|------|------|-----------|------|-------------|-------------------|
| 审计日志 | `src/features/audit/pages/AuditLogsPage.tsx` | 194-202 | 裸 Container 塌缩 | **缺**（`useAuditLogs` 第132行只取 data/isLoading/error） | title="审计日志" / `BREADCRUMBS`(25行) |
| 用户管理 | `src/features/admin/pages/UserManagementPage.tsx` | 208-216 | 裸 Container 塌缩 | **缺**（`useUsers` 第111行同上） | title="用户管理" / `BREADCRUMBS`(23行) |
| 模型详情 | `src/features/models/pages/ModelDetailPage.tsx` | 105-113 | 裸 Container 塌缩 | 有（第59行 `useModel`） | title=`{model.model_name}`（error 时无 model，需固定标题"模型详情"）/ `breadcrumbs` |
| 模型版本 | `src/features/models/pages/ModelVersionsPage.tsx` | 109-116 + 列表降级 | `if(!model)` 塌缩 + **versions 列表 error 降级为空**（`useModelVersions` 第55行未取 error，列表用 `versionsData?.versions \|\| []`） | 有（第55行） | title=`{model.model_name} - 版本历史`（!model 时需固定标题）/ `breadcrumbs` |
| 资源使用报表 | `src/features/reports/pages/ResourceUsageReportPage.tsx` | 276-284 | 裸 Container 塌缩 | 有（第204行 `useResourceUsage`） | title="资源使用报表" / `BREADCRUMBS`(33行) |
| 成本分析 | `src/features/reports/pages/CostAnalysisPage.tsx` | 309-317 | 裸 Container 塌缩 | 有（第284行 `useCostAnalysis`） | title="成本分析" / `BREADCRUMBS`(36行) |
| 监控仪表盘 | `src/features/monitoring/pages/MonitoringDashboardPage.tsx` | 497-505 | 裸 Container 塌缩（仅检查 clustersError，其余 query error 忽略） | **缺**（`useClusters` 约459行只取 data/isLoading/error，需补 refetch） | title="集群监控" / `BREADCRUMBS`(约42行，首页→资源监控) |

**通用注意**：
- 改造后检查裸 `Container`/`Box`/`Spinner` 等 import 是否仍被 loading 态或其他处使用，未使用则清理（避免 lint 报未使用 import）。
- error 态固定标题的页面（detail/versions），面包屑变量若在 early-return 之后定义，需确认作用域（参照批次 0：TrainingJobDetailPage 的 breadcrumbs 在 error 块之前定义，作用域 OK；逐页确认）。
- 每个任务只 add 本任务文件，不裹入工作区他人未提交改动。

**范围边界（本计划不做）**：monitoring/cost-analysis 的图表量纲混用（F-009/010/012/013）是独立的图表数据建模问题，不在 error 态统一范围；empty 态 CTA、shared 页居中等 P1/P2 也不在本计划。

---

### Task 1: A 类——已有 refetch 的塌缩页（ModelDetail + 2 个 reports 页）

**Files:**
- Modify: `src/features/models/pages/ModelDetailPage.tsx`
- Modify: `src/features/reports/pages/ResourceUsageReportPage.tsx`
- Modify: `src/features/reports/pages/CostAnalysisPage.tsx`
- Modify/Create: 三页对应测试（`tests/unit/features/{models,reports}/`）

这三页都已解构 refetch，error 块都是裸 Container 塌缩，改造方式同批次 0 的 TrainingJobDetailPage。

- [ ] **Step 1: 逐页写/改失败测试**

先查现有测试：`find tests -ipath '*models*' -iname '*ModelDetail*'`、`find tests -ipath '*reports*'`。对每页（用 vi.mock 模式让对应 hook 返回 `{ data: undefined, isLoading: false, error: { message: '服务器内部错误' }, refetch: vi.fn() }`）断言：
```tsx
expect(await screen.findByText('加载失败')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
```
现有测试若已有 error 用例则追加这两条断言；无则新建。

- [ ] **Step 2: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/models/ tests/unit/features/reports/ 2>&1 | tail -20
```
Expected: 新增的"加载失败"/重试断言 FAIL。

- [ ] **Step 3: 逐页改造 error 块**

- ModelDetailPage（约105-113行）：error 时无 model，用固定标题：
```tsx
if (error || !model) {
  return (
    <PageLayout title="模型详情" breadcrumbs={breadcrumbs}>
      <InlineErrorState
        title={error ? '加载失败' : '模型不存在'}
        message={error?.message ?? '未找到该模型，它可能已被删除。'}
        onRetry={error ? () => refetch() : undefined}
      />
    </PageLayout>
  );
}
```
- ResourceUsageReportPage（约276-284行）、CostAnalysisPage（约309-317行）：列表/报表型，error 时有固定标题与 breadcrumbs：
```tsx
if (error) {
  return (
    <PageLayout title="<资源使用报表|成本分析>" breadcrumbs={BREADCRUMBS}>
      <InlineErrorState message={error.message} onRetry={() => refetch()} />
    </PageLayout>
  );
}
```
每页补 import `InlineErrorState`（与 PageLayout 同行 from `@shared/components`），清理不再使用的 Container/Box import。

- [ ] **Step 4: 运行确认通过 + tsc/lint**

```bash
cd frontend && npm test -- --run tests/unit/features/models/ tests/unit/features/reports/ 2>&1 | tail -10
cd frontend && npx tsc --noEmit 2>&1 | tail -3 && npm run lint 2>&1 | tail -3
```
Expected: 全 PASS，tsc/lint 通过。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/models/pages/ModelDetailPage.tsx frontend/src/features/reports/pages/ResourceUsageReportPage.tsx frontend/src/features/reports/pages/CostAnalysisPage.tsx frontend/tests/unit/features/models/ frontend/tests/unit/features/reports/
git commit -m "fix(frontend): 模型详情/报表页错误态保留骨架并统一为 InlineErrorState（F-005/F-011）"
```

---

### Task 2: B 类——缺 refetch 解构的塌缩页（AuditLogs + UserManagement）

**Files:**
- Modify: `src/features/audit/pages/AuditLogsPage.tsx`
- Modify: `src/features/admin/pages/UserManagementPage.tsx`
- Modify/Create: 两页测试

这两页 error 块是裸 Container 塌缩，但 `useAuditLogs`/`useUsers` 解构**未取 refetch**，需先补。

- [ ] **Step 1: 写失败测试**

查现有测试，vi.mock 让 hook 返回 error + refetch。断言同 Task 1（"加载失败" + 重试按钮）。

- [ ] **Step 2: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/audit/ tests/unit/features/admin/ 2>&1 | tail -15
```

- [ ] **Step 3: 改造**

两页先在 hook 解构补 `refetch`：
- AuditLogsPage 约132行 `const { data, isLoading, error } = useAuditLogs(filters);` → 加 `refetch`
- UserManagementPage 约111行 `const { data, isLoading, error } = useUsers(filters);` → 加 `refetch`

再改 error 块（裸 Container → PageLayout 骨架内 InlineErrorState）：
```tsx
if (error) {
  return (
    <PageLayout title="<审计日志|用户管理>" breadcrumbs={BREADCRUMBS}>
      <InlineErrorState message={error.message} onRetry={() => refetch()} />
    </PageLayout>
  );
}
```
补 import InlineErrorState，清理未使用 import。注意 UserManagementPage 用了 `content` 变量模式（error 块后是 `const content = ...`），error 块在其之前 early-return，改造不影响 content。

- [ ] **Step 4: 运行确认通过 + tsc/lint**

```bash
cd frontend && npm test -- --run tests/unit/features/audit/ tests/unit/features/admin/ 2>&1 | tail -10
cd frontend && npx tsc --noEmit 2>&1 | tail -3 && npm run lint 2>&1 | tail -3
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/audit/pages/AuditLogsPage.tsx frontend/src/features/admin/pages/UserManagementPage.tsx frontend/tests/unit/features/audit/ frontend/tests/unit/features/admin/
git commit -m "fix(frontend): 审计日志/用户管理错误态保留骨架并补重试（F-007/F-014）"
```

---

### Task 3: C 类——ModelVersionsPage（error 降级为空 + !model 塌缩）

**Files:**
- Modify: `src/features/models/pages/ModelVersionsPage.tsx`
- Modify/Create: 对应测试

此页两个问题：(a) `if (!model)` 裸 Container 塌缩；(b) versions 列表的 error 被降级为空（`useModelVersions` 未解构 error，列表用 `versionsData?.versions || []` 回退）——对应审计 F-006。

- [ ] **Step 1: 理解数据流**

- 第38行 `const { data: model, isLoading: modelLoading } = useModel(modelId);` —— model 是页头依赖
- 第55行 `const { data: versionsData, isLoading: versionsLoading, refetch } = useModelVersions(...);` —— **未取 isError/error**
- 列表区（约161行）`versions={versionsData?.versions || []}` —— error 时静默空

修复：(a) `!model` 塌缩改为 PageLayout 骨架内 InlineErrorState；(b) `useModelVersions` 补 `isError: versionsError`，在版本列表 Container 上方插入 `{versionsError && <InlineErrorState ... onRetry={refetch} />}`，让加载失败显式报错而非空表。

- [ ] **Step 2: 写失败测试**

vi.mock：用例 A 让 `useModel` 返回 error/无 model → 断言固定标题骨架 + InlineErrorState；用例 B 让 `useModel` 正常但 `useModelVersions` 返回 `{ isError: true, refetch: vi.fn() }` → 断言版本区出现"加载失败"+重试，而非空表静默。

- [ ] **Step 3: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/models/ 2>&1 | tail -15
```

- [ ] **Step 4: 改造**

```tsx
// (a) !model 塌缩（约109-116行）
if (!model) {
  return (
    <PageLayout title="模型版本历史" breadcrumbs={breadcrumbs}>
      <InlineErrorState title="模型不存在" message="未找到该模型，无法查看版本历史。" />
    </PageLayout>
  );
}

// (b) useModelVersions 补 error 解构（约55行）
const { data: versionsData, isLoading: versionsLoading, isError: versionsError, refetch } = useModelVersions(...);

// (b) 版本列表 Container 上方插入显式报错
{versionsError && (
  <InlineErrorState message="版本列表加载失败。" onRetry={() => refetch()} />
)}
```
补 import，清理未使用 import。

- [ ] **Step 5: 运行确认通过 + tsc/lint**

```bash
cd frontend && npm test -- --run tests/unit/features/models/ 2>&1 | tail -10
cd frontend && npx tsc --noEmit 2>&1 | tail -3 && npm run lint 2>&1 | tail -3
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/models/pages/ModelVersionsPage.tsx frontend/tests/unit/features/models/
git commit -m "fix(frontend): 模型版本页错误态显式报错，列表加载失败不再静默降级为空（F-006）"
```

---

### Task 4: D 类——MonitoringDashboardPage（多 query error 态塌缩）

**Files:**
- Modify: `src/features/monitoring/pages/MonitoringDashboardPage.tsx`
- Modify/Create: 对应测试

此页 error 块（约498-506行）是裸 Container 塌缩，且仅检查 `clustersError`，其余 query（utilization/alerts/metrics）error 被忽略。**本任务只统一 error 态塌缩为骨架内 InlineErrorState；不碰图表量纲问题（F-009/010 独立）。**

- [ ] **Step 1: 确认勘察事实（已核验）**

已核实：error 块约 497-505 行 `if (clustersError) return 裸 Container`；`useClusters()` 约 459 行解构为 `const { data: clustersData, isLoading: clustersLoading, error: clustersError } = useClusters();`——**未取 refetch，改造时需补**；PageLayout title="集群监控"（约514行），breadcrumbs=`BREADCRUMBS` 常量（约42行）。保持现有 error 触发条件（clustersError 为主），只把塌缩展示改为骨架内 InlineErrorState。

- [ ] **Step 2: 写失败测试**

vi.mock monitoring api hook 让 clusters 查询返回 error + refetch，断言骨架内"加载失败"+重试。

- [ ] **Step 3: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/monitoring/ 2>&1 | tail -15
```

- [ ] **Step 4: 改造 error 块**

先在 `useClusters()` 解构（约459行）补 `refetch`：`const { data: clustersData, isLoading: clustersLoading, error: clustersError, refetch } = useClusters();`
再把裸 Container（约497-505行）改为：
```tsx
if (clustersError) {
  return (
    <PageLayout title="集群监控" breadcrumbs={BREADCRUMBS}>
      <InlineErrorState message={clustersError.message} onRetry={() => refetch()} />
    </PageLayout>
  );
}
```
补 import InlineErrorState，清理未使用 import。

- [ ] **Step 5: 运行确认通过 + tsc/lint**

```bash
cd frontend && npm test -- --run tests/unit/features/monitoring/ 2>&1 | tail -10
cd frontend && npx tsc --noEmit 2>&1 | tail -3 && npm run lint 2>&1 | tail -3
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/monitoring/pages/MonitoringDashboardPage.tsx frontend/tests/unit/features/monitoring/
git commit -m "fix(frontend): 监控仪表盘错误态保留骨架并统一为 InlineErrorState（F-008）"
```

---

### Task 5: 全量回归 + 截图回归

- [ ] **Step 1: 全量回归**

```bash
cd frontend && npm run lint && npx tsc --noEmit && npm test -- --run 2>&1 | tail -5
```
Expected: lint 0 警告、tsc 通过、单元测试全绿。

- [ ] **Step 2: 截图回归（验证 7 页 error 态修复）**

```bash
cd frontend && AUDIT_DATE=$(date +%F) npm run audit:screens -- --grep "(audit|admin|models/model-detail|models/model-versions|reports/resource-usage|reports/cost-analysis|monitoring)" 2>&1 | tail -5
```
用 Read 抽看 3-4 张 error 截图（如 `audit-logs--error--light.png`、`model-versions--error--light.png`、`monitoring--error--light.png`），确认：error 态保留页面骨架（侧导航/面包屑/标题）+ 统一错误 Alert + 重试按钮，不再裸文本塌缩。

- [ ] **Step 3: 汇报**

汇总修复页面数、回归结果、截图核验结论。建议下一步可对这些模块重跑 `/ui-audit` 看评分提升。

---

## 验收清单（计划级 DoD）

- [ ] 7 个页面 error 态全部改为 PageLayout 骨架内 InlineErrorState（保留标题/面包屑 + 重试）
- [ ] ModelVersionsPage 版本列表 error 不再静默降级为空（F-006）
- [ ] 各页新增/补充的 error 态测试通过
- [ ] `npm run lint`、`npx tsc --noEmit`、`npm test -- --run` 全绿
- [ ] 截图回归确认 error 态不再塌缩
- [ ] 全程 TDD（先失败测试后实现）

## 不在本计划内

- monitoring/cost-analysis 图表量纲混用（F-009/010/012/013）——独立的图表数据建模任务
- empty 态 CTA 补全（F-041 等）、shared 页垂直居中（F-035）、术语统一（F-031）、品牌化（F-049）等 P1/P2
- training-list 改用 InlineErrorState（批次 0 Task 5 可选项，已是良好样板）
