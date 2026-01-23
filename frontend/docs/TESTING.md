# 前端测试规范

> 测试分层策略、目录结构、命名规范和工具使用指南

## 测试分层策略

| 层级 | 目录 | 覆盖范围 | 运行频率 |
|------|------|---------|---------|
| **Unit** | `tests/unit/` | 组件、Hooks、工具函数、Store | 每次提交 |
| **Integration** | `tests/integration/` | API 调用、页面集成 | 每次 PR |
| **E2E** | `e2e/` | 完整用户流程 | 部署前 |

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

---

## 目录结构

```
project/
├── src/                        # 生产代码
├── tests/                      # 单元 + 集成测试 (与 src 平行)
│   ├── tsconfig.json           # 测试专用 TS 配置
│   ├── setup.ts                # Vitest 全局配置 + MSW Server
│   ├── unit/                   # 单元测试 (镜像 src 结构)
│   │   ├── app/router/         # 路由守卫测试
│   │   ├── features/           # 功能模块测试
│   │   │   ├── training/
│   │   │   ├── datasets/
│   │   │   └── models/
│   │   ├── layouts/            # 布局组件测试
│   │   ├── shared/             # 共享模块测试
│   │   ├── lib/query/          # Query 配置测试
│   │   └── store/slices/       # Store 测试
│   ├── integration/            # 集成测试
│   │   ├── api/                # API 集成测试 (MSW)
│   │   └── pages/              # 页面集成测试
│   └── __utils__/              # 测试工具
│       ├── test-utils.tsx      # 渲染包装器
│       ├── server.ts           # MSW Server 配置
│       └── mocks/
│           ├── handlers/       # MSW API handlers
│           ├── data/           # Mock 数据
│           └── stores/         # Mock Stores
└── e2e/                        # E2E 测试 (Playwright)
    ├── pages/                  # Page Objects
    ├── tests/                  # 测试用例
    ├── fixtures/               # 测试夹具
    └── utils/                  # E2E 工具
```

---

## 命名规范

### 测试文件

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 组件测试 | `{ComponentName}.test.tsx` | `Navigation.test.tsx` |
| Hook 测试 | `{useHookName}.test.ts` | `useTrainingJobs.test.ts` |
| 工具函数 | `{utilName}.test.ts` | `queryKeys.test.ts` |
| API 集成 | `{resource}Api.integration.test.ts` | `trainingJobApi.integration.test.ts` |
| 页面集成 | `{PageName}.integration.test.tsx` | `TrainingList.integration.test.tsx` |

### 测试描述

```typescript
describe('组件/模块名', () => {
  describe('功能分组', () => {
    it('应该 + 预期行为', () => {});
  });
});

// 示例
describe('TrainingJobTable', () => {
  describe('渲染', () => {
    it('应该显示任务列表', () => {});
    it('应该显示空状态提示', () => {});
  });

  describe('交互', () => {
    it('应该支持行选择', () => {});
  });
});
```

---

## 测试工具

### 路径别名

| 别名 | 路径 |
|------|------|
| `@tests/` | `tests/` |
| `@features/` | `src/features/` |
| `@shared/` | `src/shared/` |
| ... | (继承 src 所有别名) |

### 渲染包装器

```typescript
import { render, renderWithQuery } from '@tests/__utils__/test-utils';

// 完整 Provider (QueryClient + Router)
const { queryClient } = render(<MyComponent />, {
  routerProps: { initialEntries: ['/training'] },
});

// 仅 QueryClient
renderWithQuery(<MyHookConsumer />);
```

### MSW 动态覆盖

```typescript
import { server } from '@tests/__utils__/server';
import { http, HttpResponse } from 'msw';

it('应该处理 API 错误', async () => {
  // 临时覆盖 handler
  server.use(
    http.get('/api/v1/training-jobs', () => {
      return HttpResponse.json({ detail: '服务器错误' }, { status: 500 });
    })
  );

  // 测试错误处理逻辑...
});
```

### Mock Store

```typescript
import { createMockAuthStore, mockUsers, setMockToken } from '@tests/__utils__/mocks/stores/mockAuthStore';

beforeEach(() => {
  setMockToken();
});

it('应该显示管理员功能', () => {
  const authStore = createMockAuthStore(mockUsers.admin);
  // ...
});
```

---

## 命令参考

```bash
# 单元测试
npm test                        # 监听模式
npm test -- --run               # 单次运行
npm test -- tests/unit/xxx      # 运行单个文件

# 覆盖率
npm run test:coverage

# E2E 测试
npm run test:e2e                # Headless 模式
npm run test:e2e:ui             # UI 模式
npm run test:e2e:debug          # 调试模式
```

---

## 最佳实践

### ✅ 推荐

- 使用 `renderWithProviders` 确保测试隔离
- 使用 `waitFor` 处理异步状态
- Mock 外部依赖，不 Mock 内部实现
- 测试用户行为，而非实现细节

### ❌ 避免

- 测试实现细节（如内部状态）
- 过度 Mock 导致测试与真实行为偏离
- 测试文件中硬编码 API 路径
- 跳过测试而非修复问题

---

## 覆盖率目标

| 指标 | 目标 |
|------|------|
| Statements | ≥ 80% |
| Branches | ≥ 75% |
| Functions | ≥ 80% |
| Lines | ≥ 80% |

**关键模块** (shared/, lib/): ≥ 90%
