# 批次 0 快赢修复：DevTools 泄漏 + error 态统一（批次 1 范围）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 React Query DevTools 泄漏到生产（F-020），并建立统一的 `InlineErrorState` 组件替换批次 1 范围页面的 early-return 裸错误块（F-001/021/022/030 等）。

**Architecture:** 两条独立修复线。线 A：给 `<ReactQueryDevtools>` 加 `import.meta.env.DEV` 守卫。线 B：新建 `InlineErrorState` 共享组件（Cloudscape Alert + 重试，置于 PageLayout 骨架内），改造批次 1 页面——training-detail（塌缩→骨架内错误）、dashboard/home（静默降级→显式报错）。全程 TDD：先写失败测试，再实现。

**Tech Stack:** React 18 + TypeScript + Cloudscape + Vitest + Testing Library + MSW

**Spec/审计依据:** `frontend/docs/audit/2026-06-13-baseline/findings.md`（F-020, F-001, F-021, F-022, F-030）

---

## 背景知识（执行者必读）

**项目约定**：文档/注释/commit 用中文；commit 格式 `<类型>(<范围>): <描述>`，范围用 `frontend`。TDD 强制：Red→Green→Refactor，切勿为通过测试伪造结果。

**关键事实（已勘察确认）**：

| 事项 | 位置/结论 |
|------|----------|
| DevTools 泄漏点 | `src/app/providers/QueryProvider.tsx:27` 无条件渲染 `<ReactQueryDevtools initialIsOpen={false} />`；注释已写"仅开发环境"但代码无守卫 |
| 良好 error 态样板 | `src/features/training/pages/TrainingJobListPage.tsx:117-126`：PageLayout 内渲染 `<Alert type="error" header="加载失败" action={重试}>`，保留过滤器与骨架 |
| 塌缩样板（待修） | `src/features/training/pages/TrainingJobDetailPage.tsx:157-166`：`if (error \|\| !job) return <Container><Box color="text-status-error">...</Box></Container>`，绕过 PageLayout |
| 静默降级（待修） | `src/features/dashboard/pages/HomePage.tsx`：7 个 useQuery 均不检查 error，用 `?? 0` 回退；系统状态硬编码"运行正常"（约 238-240 行） |
| 共享组件目录 | `src/shared/components/feedback/`（已有 ErrorBoundary/ErrorPage/PageSpinner），导出经 `feedback/index.ts` → `shared/components/index.ts` |
| PageLayout 接口 | `title/description/actions/counter/breadcrumbs/hero/heroExtra/children`，error 态应作为 children 渲染在其内部 |
| 测试位置 | `tests/unit/shared/components/`（如 PageLayout.test.tsx），`tests/unit/features/<module>/` |
| 测试渲染器 | `@tests/__utils__/test-utils` 的 `renderWithProviders`（`render` 是其别名，二者等价；与同目录测试一致优先用 `renderWithProviders`） |
| **页面测试 mock 模式** | **全项目 page 测试统一用 `vi.mock('@features/<module>/api')` 直接 mock query hook 返回值，不用 MSW**。制造 error 态 = 让 hook 返回 `{ data: undefined, isError: true, error: { message: '...' }, refetch: vi.fn() }`。本计划所有页面测试一律遵循此模式 |
| training detail 测试现状 | `tests/unit/features/training/TrainingJobDetailPage.test.tsx` **已存在**，已有"错误状态"describe 块（约 357-370 行）用 `mockUseTrainingJob.mockReturnValue({ error: { message: '训练任务不存在' } })`。本计划是**改造/追加**该测试，非新建 |
| dashboard 测试现状 | **不存在** `tests/unit/features/dashboard/` 目录。HomePage 测试需**新建**。HomePage 用 `useTrainingJobs/useDatasets/useModels` 跨模块 hook + `useAuthStore`，mock 这些 api 模块制造 error；auth 参考 `tests/__utils__/mocks/stores/` |
| HomePage 两处硬编码健康 | 系统状态面板约 239 行"运行正常"；**另有 heroExtra 约 150 行 `<StatusIndicator type="success">平台服务运行正常</StatusIndicator>`**，两处都需在 error 态降级 |

**范围边界（本计划只做）**：DevTools 守卫 + InlineErrorState 组件 + 改造 training-detail、dashboard/home 两个批次 1 页面。training-list 已是良好样板（仅可选地改用新组件保持一致，列为可选步骤）。其余 P0 页面（audit/admin/models/reports/monitoring 等）留待阶段 4 批量替换——本计划证明组件可用即可。

---

## 文件结构总览

```
新建:
  src/shared/components/feedback/InlineErrorState.tsx   # 统一内联错误组件
  tests/unit/shared/components/feedback/InlineErrorState.test.tsx

修改:
  src/app/providers/QueryProvider.tsx                   # DevTools 加 DEV 守卫
  src/shared/components/feedback/index.ts               # 导出 InlineErrorState
  src/shared/components/index.ts                        # 二次导出
  src/features/training/pages/TrainingJobDetailPage.tsx # 塌缩→骨架内错误
  src/features/dashboard/pages/HomePage.tsx             # 静默降级→显式报错
  tests/unit/features/training/...DetailPage 测试        # 若存在则补 error 态断言
  tests/unit/features/dashboard/...HomePage 测试         # 若存在则补 error 态断言
```

---

### Task 1: 分支/worktree 与 DevTools 守卫（线 A，独立可交付）

**Files:**
- Modify: `frontend/src/app/providers/QueryProvider.tsx`

- [ ] **Step 1: 创建隔离工作区**

本计划动 `src/` 生产代码，且当前 `feature/ui-audit-infrastructure` 分支混入了他人提交。从 `main` 切一个干净的修复分支：

```bash
cd /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project
git checkout main && git checkout -b fix/ui-batch0-error-states
```

若 `main` 缺少本计划依赖的 audit 报告文件（findings.md），不影响——本计划改的是 `src/`，审计报告仅作参考依据。工作区有他人未提交改动时，**只 add 本计划涉及的文件**。

- [ ] **Step 2: 写失败测试（DevTools 不应在生产渲染）**

由于 DevTools 行为依赖 `import.meta.env.DEV`，单元测试中 jsdom 环境 DEV 默认为 true，难以直接断言"生产不渲染"。改为**代码层面验证**：测试 QueryProvider 在 DEV=false 时不抛错且正常渲染 children。先写一个会失败的断言（验证守卫存在）：

`tests/unit/app/providers/QueryProvider.test.tsx`（若目录不存在则创建）：

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@tests/__utils__/test-utils';
import { QueryProvider } from '@/app/providers/QueryProvider';

describe('QueryProvider', () => {
  it('应正常渲染子内容', () => {
    render(
      <QueryProvider>
        <div>子内容</div>
      </QueryProvider>,
    );
    expect(screen.getByText('子内容')).toBeInTheDocument();
  });

  it('源码应使用 import.meta.env.DEV 守卫 DevTools（防止泄漏到生产）', async () => {
    // 读取源码断言守卫存在——DevTools 行为无法在 jsdom 直接验证，故用静态断言兜底
    const fs = await import('node:fs');
    const src = fs.readFileSync(
      new URL('../../../../src/app/providers/QueryProvider.tsx', import.meta.url),
      'utf-8',
    );
    expect(src).toMatch(/import\.meta\.env\.DEV\s*&&\s*<ReactQueryDevtools/);
  });
});
```

注意：上面相对路径需按测试文件实际位置调整到指向 `src/app/providers/QueryProvider.tsx`。若项目测试规范不鼓励读源码断言，可改用对 `render(<QueryProvider>)` 输出做 DOM 查询（DEV 下应有 devtools 按钮、可通过 `vi.stubEnv('DEV', false)` 重渲染断言消失）——优先用 `vi.stubEnv` 方案，更贴近行为测试。

- [ ] **Step 3: 运行测试确认失败**

```bash
cd frontend && npm test -- --run tests/unit/app/providers/QueryProvider.test.tsx 2>&1 | tail -15
```

Expected: 守卫断言 FAIL（当前代码无 DEV 守卫）。

- [ ] **Step 4: 实现守卫**

`QueryProvider.tsx` 第 27 行改为：

```tsx
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd frontend && npm test -- --run tests/unit/app/providers/QueryProvider.test.tsx 2>&1 | tail -10
```

Expected: PASS。

- [ ] **Step 6: 验证生产构建不含 devtools**

```bash
cd frontend && npm run build 2>&1 | tail -5 && grep -rl "initialIsOpen" dist/assets/ 2>/dev/null && echo "❌ devtools 仍在 bundle" || echo "✅ devtools 已从生产 bundle 移除"
```

Expected: 输出"✅ devtools 已从生产 bundle 移除"。（Vite 对 `import.meta.env.DEV && ...` 在生产构建时做死代码消除。）

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/providers/QueryProvider.tsx frontend/tests/unit/app/providers/QueryProvider.test.tsx
git commit -m "fix(frontend): React Query DevTools 仅开发环境加载，修复生产界面悬浮按钮泄漏"
```

---

### Task 2: InlineErrorState 共享组件（TDD）

**Files:**
- Create: `frontend/src/shared/components/feedback/InlineErrorState.tsx`
- Create: `frontend/tests/unit/shared/components/feedback/InlineErrorState.test.tsx`
- Modify: `frontend/src/shared/components/feedback/index.ts`
- Modify: `frontend/src/shared/components/index.ts`

- [ ] **Step 1: 写失败测试**

`tests/unit/shared/components/feedback/InlineErrorState.test.tsx`：

```tsx
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@tests/__utils__/test-utils';
import { InlineErrorState } from '@shared/components';

describe('InlineErrorState', () => {
  it('应渲染错误标题与消息', () => {
    render(<InlineErrorState message="服务器内部错误" />);
    expect(screen.getByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('服务器内部错误')).toBeInTheDocument();
  });

  it('提供 onRetry 时应渲染重试按钮并可点击', async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<InlineErrorState message="网络错误" onRetry={onRetry} />);
    const btn = screen.getByRole('button', { name: '重试' });
    await user.click(btn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('未提供 onRetry 时不渲染重试按钮', () => {
    render(<InlineErrorState message="错误" />);
    expect(screen.queryByRole('button', { name: '重试' })).not.toBeInTheDocument();
  });

  it('支持自定义标题', () => {
    render(<InlineErrorState title="资源不存在" message="找不到该任务" />);
    expect(screen.getByText('资源不存在')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd frontend && npm test -- --run tests/unit/shared/components/feedback/InlineErrorState.test.tsx 2>&1 | tail -10
```

Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现组件**

`src/shared/components/feedback/InlineErrorState.tsx`：

```tsx
/**
 * InlineErrorState 组件
 *
 * 统一的页面内联错误状态——在 PageLayout 骨架内部渲染，
 * 保留页面 Header/面包屑/操作区，提供 Cloudscape Alert + 重试入口。
 *
 * 用于 query 错误场景，替代各页面 early-return 的裸 Container 错误块。
 * 错误态绝不静默降级为空数据；失败时应抑制 empty 态内容。
 */

import { Alert, Button } from '@cloudscape-design/components';

export interface InlineErrorStateProps {
  /** 错误描述（通常为 error.message） */
  message?: string;
  /** 错误标题，默认"加载失败" */
  title?: string;
  /** 重试回调；提供时渲染"重试"按钮（通常传 query 的 refetch） */
  onRetry?: () => void;
}

export function InlineErrorState({
  message,
  title = '加载失败',
  onRetry,
}: InlineErrorStateProps) {
  return (
    <Alert
      type="error"
      header={title}
      action={onRetry ? <Button onClick={onRetry}>重试</Button> : undefined}
    >
      {message ?? '发生未知错误，请稍后重试。'}
    </Alert>
  );
}
```

- [ ] **Step 4: 导出组件**

`src/shared/components/feedback/index.ts` 追加：

```typescript
export { InlineErrorState } from './InlineErrorState';
export type { InlineErrorStateProps } from './InlineErrorState';
```

`src/shared/components/index.ts` 在 Notification 段后追加：

```typescript
// Feedback
export { InlineErrorState } from './feedback';
export type { InlineErrorStateProps } from './feedback';
```

注意：先确认 `shared/components/index.ts` 当前是否已 re-export feedback（勘察显示它只导出了 forms/StatusBadge/PageLayout/NotificationCenter，未导出 feedback）。若 feedback 未被二次导出，按上面追加；保持与现有导出风格一致。

- [ ] **Step 5: 运行测试确认通过**

```bash
cd frontend && npm test -- --run tests/unit/shared/components/feedback/InlineErrorState.test.tsx 2>&1 | tail -10
```

Expected: 4 个测试全 PASS。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/shared/components/feedback/InlineErrorState.tsx frontend/src/shared/components/feedback/index.ts frontend/src/shared/components/index.ts frontend/tests/unit/shared/components/feedback/InlineErrorState.test.tsx
git commit -m "feat(frontend): 新增 InlineErrorState 统一内联错误组件（Alert + 重试）"
```

---

### Task 3: 改造 TrainingJobDetailPage error 态（塌缩→骨架内）

**Files:**
- Modify: `frontend/src/features/training/pages/TrainingJobDetailPage.tsx`
- Modify: `frontend/tests/unit/features/training/TrainingJobDetailPage.test.tsx`（已存在，改造其"错误状态"块）

- [ ] **Step 1: 改造现有 error 测试（vi.mock 模式，非 MSW）**

该测试**已存在**且用 `vi.mock('@features/training/api')` 模式。打开它，定位现有"错误状态"describe 块（约 357-370 行），它已用 `mockUseTrainingJob.mockReturnValue({ error: { message: '训练任务不存在' } })` 断言 `getByText(/训练任务不存在/)`。在此基础上**追加**对统一错误组件的断言（保持 vi.mock 模式，不引入 MSW）：

```tsx
// 在现有"错误状态"块中追加（error mock 已设置好，message 为 '训练任务不存在'）：
expect(await screen.findByText('加载失败')).toBeInTheDocument();          // InlineErrorState 标题
expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();  // 重试按钮
// 原有的 getByText(/训练任务不存在/) 断言保留——InlineErrorState 的 message 仍渲染它
```

注意 mock 需提供 `refetch: vi.fn()`（InlineErrorState 的重试按钮 onRetry 调用它）。若现有 mock 未含 refetch，补上。
detail 页 error 时拿不到 `job.job_name` 作标题——改造方案是 error 态用**带固定标题的 PageLayout**（title="训练任务详情" + 保留 breadcrumbs）包裹 InlineErrorState，而非裸 Container。

- [ ] **Step 2: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/training/TrainingJobDetailPage.test.tsx 2>&1 | tail -15
```

Expected: 新增的"加载失败"/重试按钮断言 FAIL（当前是裸 Container，无标题/重试按钮）；原有 `/训练任务不存在/` 断言可能仍通过。

- [ ] **Step 3: 改造 error 分支**

`TrainingJobDetailPage.tsx` 的 `if (error || !job)` 分支（约 157-166 行）从裸 Container 改为 PageLayout 骨架内的 InlineErrorState：

```tsx
  // 错误状态：保留页面骨架（标题/面包屑），提供重试
  if (error || !job) {
    return (
      <PageLayout
        title="训练任务详情"
        breadcrumbs={breadcrumbs}
      >
        <InlineErrorState
          title={error ? '加载失败' : '任务不存在'}
          message={error?.message ?? '未找到该训练任务，它可能已被删除。'}
          onRetry={error ? () => refetch() : undefined}
        />
      </PageLayout>
    );
  }
```

确认该文件已 import：`PageLayout`、`InlineErrorState`（从 `@shared/components`）、以及 `breadcrumbs`/`refetch` 在作用域内可用（refetch 来自 useQuery 返回；若当前未解构出 refetch，需补上）。删除不再需要的裸 Container/Box import（若仅此处用到）。

- [ ] **Step 4: 运行确认通过**

```bash
cd frontend && npm test -- --run tests/unit/features/training/TrainingJobDetailPage.test.tsx 2>&1 | tail -10
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/training/pages/TrainingJobDetailPage.tsx frontend/tests/unit/features/training/TrainingJobDetailPage.test.tsx
git commit -m "fix(frontend): 训练详情页错误态保留骨架并统一为 InlineErrorState（F-021）"
```

---

### Task 4: 修复 HomePage 静默降级（error 态显式报错）

**Files:**
- Modify: `frontend/src/features/dashboard/pages/HomePage.tsx`
- Create: `frontend/tests/unit/features/dashboard/HomePage.test.tsx`（目录与测试均不存在，需新建）

- [ ] **Step 1: 理解现状并设计修复**

HomePage 有 7 个 useQuery（来自 `useTrainingJobs/useDatasets/useModels` 跨模块 hook），全部只取 `data`/`isLoading`、**不解构 error**，用 `?? 0` 回退；**两处**硬编码健康：heroExtra 约 150 行 `平台服务运行正常`、系统状态面板约 239 行 `运行正常`。修复目标（最小且不破坏正常态）：
- 解构关键 query（至少 allJobs，即驱动核心指标的 `useTrainingJobs` 查询）的 `isError`/`error`/`refetch`，聚合为 `hasError`；
- `hasError` 时在 PageLayout 内、指标区之前渲染 `InlineErrorState`（带重试，onRetry 调 refetch）；
- 两处"运行正常"都改为依赖 `hasError`——失败时降级为 `<StatusIndicator type="warning">无法获取</StatusIndicator>` + 对应文案。

保持 default/loading 态完全不变（loading 仍显示骨架"—"）。

- [ ] **Step 2: 新建失败测试（vi.mock 模式，非 MSW）**

`tests/unit/features/dashboard/HomePage.test.tsx` 新建。沿用项目 page 测试惯例：`vi.mock('@features/training/api')`（及 datasets/models 如被直接引用）让 `useTrainingJobs` 返回 error 态；auth 用 `tests/__utils__/mocks/stores/` 的 mock store。用 `renderWithProviders` 渲染：

```tsx
// 1. mock useTrainingJobs 返回 { data: undefined, isError: true, error: { message: '服务器内部错误' }, refetch: vi.fn() }
// 2. 断言显式报错而非静默 0
expect(await screen.findByText('加载失败')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
// 3. error 态下系统状态不再全绿——断言出现"无法获取"降级文案
expect(screen.getByText('无法获取')).toBeInTheDocument();
// 另建一个正常态测试：mock 返回正常 data，断言指标数字正常渲染、无"加载失败"
```

- [ ] **Step 3: 运行确认失败**

```bash
cd frontend && npm test -- --run tests/unit/features/dashboard/HomePage.test.tsx 2>&1 | tail -15
```

Expected: error 态断言 FAIL（当前 error 被吞，显示 0 + 全绿）。

- [ ] **Step 4: 实现修复**

在 HomePage：
1. 解构 `useTrainingJobs` 的 `isError`/`error`/`refetch`（当前只取了 data/isLoading，需补）；定义 `const hasError = isError`（或聚合多个关键 query）；
2. PageLayout 内、指标区之前插入：`{hasError && <InlineErrorState message={error?.message} onRetry={() => refetch()} />}`；
3. **两处**硬编码健康都改：heroExtra（约 150 行）与系统状态面板（约 239 行）的 `<StatusIndicator type="success">...运行正常</StatusIndicator>` 改为 `hasError ? <StatusIndicator type="warning">无法获取</StatusIndicator> : <StatusIndicator type="success">运行正常</StatusIndicator>`。

保持 hero 页头、指标卡、快速操作等正常态结构不变。

- [ ] **Step 5: 运行确认通过**

```bash
cd frontend && npm test -- --run tests/unit/features/dashboard/HomePage.test.tsx 2>&1 | tail -10
```

Expected: PASS（error 态 + 正常态测试均通过）。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/dashboard/pages/HomePage.tsx frontend/tests/unit/features/dashboard/HomePage.test.tsx
git commit -m "fix(frontend): 首页错误态显式报错，系统状态不再静默伪装健康（F-001/F-030）"
```

---

### Task 5: 回归验证 + 审计回归（可选 training-list 对齐）

**Files:**
- 可选 Modify: `frontend/src/features/training/pages/TrainingJobListPage.tsx`（改用 InlineErrorState 保持一致）

- [ ] **Step 1:（可选）training-list 改用 InlineErrorState**

training-list 现有 error 块（117-126 行）已是良好样板，仅为统一组件可替换为 `<InlineErrorState message={error.message} onRetry={() => refetch()} />`。行为等价，纯一致性收益。若替换，跑该页测试确认不回归。

- [ ] **Step 2: 全量回归**

```bash
cd frontend && npm run lint && npx tsc --noEmit && npm test -- --run 2>&1 | tail -5
```

Expected: lint 0 警告、类型通过、单元测试全绿。

- [ ] **Step 3: 审计回归（用截图流水线验证修复效果）**

本计划在 `fix/ui-batch0-error-states` 分支，可能不含 audit 流水线（它在 feature/ui-audit-infrastructure）。若 audit 流水线不在当前分支，跳过此步并说明；若在，则：

```bash
cd frontend && npm run audit:screens -- --grep "(training/training-detail|dashboard)" 2>&1 | tail -5
```

用 Read 抽看 `training-detail--error--light.png` 与 `home--error--light.png`，确认：error 态保留页面骨架、显示统一错误 Alert + 重试按钮、不再裸文本/静默全绿。

- [ ] **Step 4: Commit（若有 training-list 改动）**

```bash
git add -A && git commit -m "refactor(frontend): 训练列表页错误态统一改用 InlineErrorState"
```

---

## 验收清单（计划级 DoD）

- [ ] `npm run build` 后 `dist/` 不含 `initialIsOpen`（devtools 不入生产）
- [ ] InlineErrorState 组件 4 个单元测试通过
- [ ] training-detail error 态保留骨架 + 重试按钮（测试断言 + 截图佐证）
- [ ] dashboard error 态显式报错、系统状态不再静默全绿（测试断言）
- [ ] `npm run lint`、`npx tsc --noEmit`、`npm test -- --run` 全绿
- [ ] 所有改动遵循 TDD（先失败测试，后实现）

## 不在本计划内（留待阶段 4）

- 其余 P0 error 态塌缩页面的批量替换：audit-logs、user-management、model-detail、model-versions、resource-usage、cost-analysis、monitoring（共 7+ 页）——本计划证明 InlineErrorState 可用，阶段 4 按 findings 清单批量替换
- monitoring/cost-analysis 图表量纲修复（F-009/010/012/013）
- empty 态 CTA 补全、shared 页居中、空文案统一等 P1/P2
