> **职责**: 测试规范 - TDD 工作流、测试分层、覆盖率要求

# 测试规范 (Testing Standards)

---

## 0. 速查卡片

### 命令

```bash
npm test                        # 监听模式
npm test -- --run               # 单次运行
npm test -- tests/unit/xxx      # 运行单个文件
npm run test:coverage           # 覆盖率报告
npm run test:e2e                # Headless 模式
npm run test:e2e:ui             # UI 模式
npm run test:e2e:debug          # 调试模式
```

### 命名

| 元素 | 模式 | 示例 |
|------|------|------|
| 组件测试 | `{ComponentName}.test.tsx` | `Navigation.test.tsx` |
| Hook 测试 | `{useHookName}.test.ts` | `useTrainingJobs.test.ts` |
| 工具函数 | `{utilName}.test.ts` | `queryKeys.test.ts` |
| API 集成 | `{resource}Api.integration.test.ts` | `trainingJobApi.integration.test.ts` |
| 页面集成 | `{PageName}.integration.test.tsx` | `TrainingList.integration.test.tsx` |
| E2E 文件 | `{feature}.spec.ts` | `auth.spec.ts` |

### 分层

| 层级 | 目录 | 覆盖范围 | Mock | 工具 | 运行频率 |
|------|------|---------|------|------|---------|
| Unit | `tests/unit/` | 组件、Hooks、工具函数、Store | 外部依赖 | Vitest + Testing Library | 每次提交 |
| Integration | `tests/integration/` | API 调用、页面集成 | 外部服务 | Vitest + MSW | 每次 PR |
| E2E | `e2e/` | 完整用户流程 | 无 | Playwright | 部署前 |

### 测试金字塔

```
        /\
       /E2E\      ← 少量，验证关键流程
      /______\
     /Integ  \    ← 中等，验证模块协作
    /__________\
   /   Unit     \  ← 大量，验证单元逻辑
  /______________\
```

### 陷阱 ⚠️

- ❌ 测试实现细节 → ✅ 测试行为
- ❌ `getByTestId` 优先 → ✅ 可访问性查询优先
- ❌ 同步期望异步 → ✅ `waitFor` / `findBy`
- ❌ 硬编码 API 路径 → ✅ 使用 MSW handler 中的常量
- ❌ Mock 内部实现 → ✅ 只 Mock 外部依赖 (API、第三方库)
- ❌ 裸渲染 (`render(<Comp />)`) → ✅ 使用 `render` from `@tests/__utils__/test-utils` 确保 Provider 隔离
- ❌ 跳过 / 注释失败测试 → ✅ 修复根因

---

## 1. 测试文件位置

> 完整目录结构详见 [project-structure.md](project-structure.md) §0

**核心约定**:
- 采用 `tests/` 独立目录，测试文件镜像 `src/` 结构
- 单元测试: `tests/unit/` | 集成测试: `tests/integration/` | E2E: `e2e/`
- 测试工具 (MSW Server, 渲染包装器, Mock): `tests/__utils__/`

---

## 2. 组件测试

### 2.1 基本模板

**约定**: `describe` 按「渲染 / 交互」分组，交互测试必须 `userEvent.setup()` 前置

```typescript
// 渲染测试
render(<TrainingJobTable jobs={mockJobs} />);
expect(screen.getByRole('table')).toBeInTheDocument();

// 交互测试 — userEvent.setup() 必须在 render 之前
const user = userEvent.setup();
render(<TrainingJobTable jobs={mockJobs} onSelect={vi.fn()} />);
await user.click(screen.getByRole('row', { name: /任务1/ }));
expect(onSelect).toHaveBeenCalledTimes(1);
```

### 2.2 查询优先级

```typescript
// ✅ 推荐 (按优先级)
screen.getByRole('button', { name: '提交' });  // 1. 角色
screen.getByLabelText('用户名');               // 2. 标签
screen.getByPlaceholderText('请输入');         // 3. 占位符
screen.getByText('欢迎');                      // 4. 文本
// ❌ 最后选择
screen.getByTestId('custom-element');
```

### 2.3 异步测试

```typescript
it('should load data', async () => {
  render(<AsyncComponent />);
  expect(await screen.findByText('加载完成')).toBeInTheDocument();
});
```

---

## 3. Hook 测试

```typescript
import { renderHook, act } from '@testing-library/react';
import { vi, beforeEach, afterEach } from 'vitest';

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('should debounce value', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'hello' } }
    );
    rerender({ value: 'world' });
    expect(result.current).toBe('hello');
    act(() => vi.advanceTimersByTime(500));
    expect(result.current).toBe('world');
  });
});
```

---

## 4. API Mock (MSW)

### 4.1 配置

```typescript
// --- handlers: tests/__utils__/mocks/handlers/training.ts ---
export const trainingHandlers = [
  http.get('/api/v1/training-jobs', () => HttpResponse.json({ items: [...], total: 1 })),
  http.post('/api/v1/training-jobs', async ({ request }) =>
    HttpResponse.json({ id: 2, ...(await request.json()) }, { status: 201 })),
];

// --- server: tests/__utils__/server.ts ---
export const server = setupServer(...trainingHandlers);

// --- setup: tests/setup.ts ---
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 4.2 动态覆盖

```typescript
// 单个测试中临时覆盖 handler
server.use(http.get('/api/v1/training-jobs', () => HttpResponse.json({ detail: '错误' }, { status: 500 })));
```

### 4.3 Mock Store

```typescript
// tests/__utils__/mocks/stores/ 提供 createMockAuthStore, mockUsers, setMockToken
beforeEach(() => setMockToken());
const authStore = createMockAuthStore(mockUsers.admin);
```

---

## 5. E2E 测试 (Playwright)

### 5.1 Page Object 模式

```typescript
export class TrainingListPage {
  constructor(private page: Page) {}
  readonly createButton = () => this.page.getByRole('button', { name: '创建任务' });
  readonly jobTable = () => this.page.getByRole('table');

  async goto() { await this.page.goto('/training'); }
  async createJob(name: string) {
    await this.createButton().click();
    await this.page.getByLabel('任务名称').fill(name);
    await this.page.getByRole('button', { name: '提交' }).click();
  }
}
```

### 5.2 基本模板

```typescript
import { test, expect } from '@playwright/test';

test.describe('Training Jobs', () => {
  test('should create a new training job', async ({ page }) => {
    const trainingPage = new TrainingListPage(page);
    await trainingPage.goto();
    await trainingPage.createJob('测试任务');
    await expect(page.getByText('任务创建成功')).toBeVisible();
  });
});
```

---

## 6. 测试配置

### 6.1 路径别名

| 别名 | 路径 |
|------|------|
| `@tests/` | `tests/` |
| `@features/` | `src/features/` |
| `@shared/` | `src/shared/` |
| ... | (继承 src 所有别名) |

### 6.2 渲染包装器

```typescript
import { render, renderWithQuery } from '@tests/__utils__/test-utils';

// 完整 Provider (QueryClient + Router)
const { queryClient } = render(<MyComponent />, {
  routerProps: { initialEntries: ['/training'] },
});

// 仅 QueryClient
renderWithQuery(<MyHookConsumer />);
```

---

## 7. 覆盖率要求

### 按组件类型

| 层级 | 最低 | 目标 |
|------|-----|------|
| Hooks | 90% | 95% |
| Components | 80% | 85% |
| Utils | 95% | 100% |
| **整体** | **80%** | **85%** |

### 按指标维度

| 指标 | 目标 |
|------|------|
| Statements | ≥ 80% |
| Branches | ≥ 75% |
| Functions | ≥ 80% |
| Lines | ≥ 80% |

**关键模块** (shared/, lib/): ≥ 90%
