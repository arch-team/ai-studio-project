# UI/UX 审计基础设施与基线审计 实施计划（阶段 0 + 阶段 1）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成截图流水线 + 评分体系 + `/ui-audit` skill + `design-reviewer` agent，并完成 13 个模块的全量基线审计，产出审计报告三件套。

**Architecture:** 在 `frontend/e2e/audit/` 下新建独立的 Playwright 截图流水线（独立 project，不混入常规 E2E），通过 route interception 全量 Mock API（含 auth），按"页面清单 × 状态 × 双主题"矩阵产出截图；评分由独立的 `design-reviewer` agent 完成（四维度加权框架），`/ui-audit` skill 负责编排"截图 → 评分 → 汇总报告"。

**Tech Stack:** Playwright（已有 1.57）、TypeScript、Claude Code skill/agent 机制

**Spec:** `docs/superpowers/specs/2026-06-12-ui-ux-quality-system-design.md`（已批准；本计划覆盖其阶段 0+1，阶段 2-4 依赖审计结果在报告产出后另行计划）

---

## 背景知识（执行者必读）

**项目约定**（来自 `frontend/CLAUDE.md` 和根 `CLAUDE.md`）：
- 所有文档、注释、commit 信息使用中文
- commit 格式：`<类型>(<范围>): <描述>`，范围用 `frontend`
- E2E 相关命令在 `frontend/` 目录下执行

**关键现有设施**（直接复用，不要重写）：

| 设施 | 路径 | 用途 |
|------|------|------|
| Playwright 配置 | `frontend/playwright.config.ts` | baseURL `http://localhost:5173`，本地模式自动启动 dev server |
| 认证注入 | `frontend/e2e/utils/auth.ts` | `sessionStorage['auth.refresh_token']` 注入后应用自动静默续期 |
| Mock 模式参考 | `frontend/e2e/utils/mockApi.ts` | route interception 写法范例（`route.fallback()` 传递、正则匹配） |
| 既有 fixtures | `frontend/e2e/fixtures/{trainingJobs,spaces,resourceQuotas}.ts` | fixture 文件的形状约定（纯对象、不 import src） |

**关键机制事实**（已勘察确认）：
- 应用启动时 `initializeAuth` 读取 `sessionStorage['auth.refresh_token']` → 调 `POST /api/v1/auth/token/refresh` → 调 `GET /api/v1/auth/me` 恢复登录态。Mock 这两个端点 + 注入 sessionStorage 即可完全脱离后端。
- `TokenResponse` 形状：`{access_token, refresh_token, token_type, expires_in}`；`UserResponse` 形状：`{id, username, email, display_name, role, status, auth_type}`（见 `frontend/src/features/auth/types/index.ts:24-46`）
- 主题由 zustand persist 控制：`localStorage['ui-storage']` = `{"state":{"sidebarOpen":true,"theme":"dark","density":"comfortable"},"version":0}`，`useThemeEffect`（`frontend/src/shared/hooks/useThemeEffect.ts`）会在启动时 `applyMode`。注入 localStorage 即可控制主题，无需点击 UI。
- 列表响应统一形状：`{items, total, page, page_size}`（架构规范 §5.2）
- Playwright route 匹配顺序：**后注册的优先**。兜底 catch-all 必须最先注册。
- billing 模块没有独立页面（`src/features/billing/pages/` 为空），manifest 中记录为"无路由"即可。

---

## 文件结构总览

```
frontend/e2e/audit/                      # 新增：审计流水线（独立目录）
├── routes-manifest.ts                   # 页面清单（28 个 PageSpec）
├── auditSetup.ts                        # auth mock + 主题注入
├── auditMockApi.ts                      # 按状态切换的通用 API mock
├── fixtures/                            # 审计专用 fixture（仅缺失模块）
│   ├── datasets.ts
│   ├── models.ts
│   ├── templates.ts
│   ├── auditLogs.ts
│   ├── users.ts
│   └── checkpoints.ts
└── screenshot-pipeline.spec.ts          # 截图流水线主程序

frontend/e2e/audit/audit-output/         # 截图产出（gitignore）

.claude/agents/design-reviewer.md        # 新增：设计评审 agent
.claude/skills/ui-audit/SKILL.md         # 新增：/ui-audit skill

frontend/docs/audit/<日期>-baseline/      # 阶段 1 产出：报告三件套
├── audit-report.md
├── findings.md
└── score-matrix.md
```

修改的现有文件：
- `frontend/playwright.config.ts`（新增 audit project、隔离常规 E2E）
- `frontend/package.json`（新增 `audit:screens` script）
- `.gitignore`（新增 audit-output）

---

### Task 1: 分支与脚手架（Playwright project 隔离 + npm script + gitignore）

**Files:**
- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/package.json`
- Modify: `.gitignore`（仓库根）

- [ ] **Step 1: 创建特性分支**

```bash
cd /Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project
git checkout -b feature/ui-audit-infrastructure
```

注意：工作区有他人未提交的改动（backend tests 等），**不要 stash、不要提交它们**，后续每次 commit 只 add 本计划涉及的文件。

- [ ] **Step 2: 修改 Playwright 配置，隔离 audit project**

`frontend/playwright.config.ts` 的 `projects` 数组改为：

```typescript
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /audit\//,
    },
    {
      name: 'audit',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
      },
      testMatch: /audit\/.*\.spec\.ts/,
    },
  ],
```

注意：`playwright test` 不带 `--project` 时会运行**所有** project（包括 audit），所以必须配合 Step 3 修改 `test:e2e` 系列脚本，否则常规 E2E 会连带跑出全部审计截图。

- [ ] **Step 3: 新增 npm script 并隔离既有 E2E 脚本**

`frontend/package.json` 的 `scripts` 中新增一条、修改三条：

```json
    "audit:screens": "playwright test --project=audit",
    "test:e2e": "playwright test --project=chromium",
    "test:e2e:ui": "playwright test --project=chromium --ui",
    "test:e2e:debug": "playwright test --project=chromium --debug",
```

- [ ] **Step 4: gitignore 截图产出**

仓库根 `.gitignore` 在 `playwright/.cache/` 行之后新增：

```
frontend/e2e/audit/audit-output/
```

- [ ] **Step 5: 验证配置不破坏现有 E2E 收集且隔离生效**

```bash
cd frontend && npx playwright test --list 2>&1 | tail -3
cd frontend && npx playwright test --project=chromium --list 2>&1 | grep -ci "audit/" || echo "隔离生效: chromium 不含 audit 测试"
```

Expected: 第一条列出现有测试（数量不为 0）无配置报错；第二条输出"隔离生效"（grep 计数为 0）。此时 audit project 还没有测试文件，属正常。

- [ ] **Step 6: Commit**

```bash
git add frontend/playwright.config.ts frontend/package.json .gitignore
git commit -m "chore(frontend): 新增 Playwright audit project 与截图产出忽略规则"
```

---

### Task 2: 页面清单 routes-manifest.ts

**Files:**
- Create: `frontend/e2e/audit/routes-manifest.ts`

页面清单是流水线的数据源。类型与 28 个页面条目如下（**完整代码**，但 `primary`/`extras` 的 API pattern 留待 Task 4-6 按模块补全——本任务先把 `primary` 全部置为 `undefined`，让矩阵骨架先立起来）：

- [ ] **Step 1: 写入 manifest 文件**

```typescript
/**
 * UI/UX 审计页面清单
 *
 * 数据源：frontend/src/app/router/routes.ts（28 个可审计页面）
 * 状态豁免规则见 spec §3.1/§5.4：
 * - 列表页: default/empty/loading/error 四态
 * - 详情页: default/loading/error 三态（error 用 404）
 * - 表单页: 仅 default（提交类错误属交互级，静态截图不适用）
 * - dashboard 类: default/loading/error
 * - 特殊页（登录/404/IDE）: 仅 default
 *
 * 注意：billing 模块无独立页面（src/features/billing/pages/ 为空），不在清单内。
 */

export type AuditState = 'default' | 'empty' | 'loading' | 'error';
export type PageType = 'list' | 'detail' | 'form' | 'dashboard' | 'special';

export interface ApiMock {
  /** 主数据 API 匹配（注意排除子路径，参考 e2e/utils/mockApi.ts 的正则写法） */
  pattern: RegExp;
  /** default 状态返回体 */
  defaultBody: unknown;
  /** empty 状态返回体（缺省用标准空列表） */
  emptyBody?: unknown;
}

export interface PageSpec {
  module: string;
  pageName: string;
  route: string;
  pageType: PageType;
  states: AuditState[];
  /** 默认 true；登录页/错误页为 false */
  requiresAuth?: boolean;
  /** 状态切换作用于此 API；undefined 表示页面无主数据 API（纯静态页） */
  primary?: ApiMock;
  /** 页面依赖的其他 API，始终返回 defaultBody */
  extras?: ApiMock[];
}

const LIST_STATES: AuditState[] = ['default', 'empty', 'loading', 'error'];
const DETAIL_STATES: AuditState[] = ['default', 'loading', 'error'];
const DASHBOARD_STATES: AuditState[] = ['default', 'loading', 'error'];

export const AUDIT_PAGES: PageSpec[] = [
  // === dashboard ===
  { module: 'dashboard', pageName: 'home', route: '/', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === auth ===
  { module: 'auth', pageName: 'login', route: '/login', pageType: 'special', states: ['default'], requiresAuth: false },

  // === training ===
  { module: 'training', pageName: 'training-list', route: '/training-jobs', pageType: 'list', states: LIST_STATES },
  { module: 'training', pageName: 'training-create', route: '/training-jobs/create', pageType: 'form', states: ['default'] },
  { module: 'training', pageName: 'training-detail', route: '/training-jobs/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'training', pageName: 'checkpoints', route: '/checkpoints', pageType: 'list', states: LIST_STATES },

  // === templates ===
  { module: 'templates', pageName: 'template-list', route: '/job-templates', pageType: 'list', states: LIST_STATES },
  { module: 'templates', pageName: 'template-detail', route: '/job-templates/1', pageType: 'detail', states: DETAIL_STATES },

  // === models ===
  { module: 'models', pageName: 'model-list', route: '/models', pageType: 'list', states: LIST_STATES },
  { module: 'models', pageName: 'model-detail', route: '/models/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'models', pageName: 'model-versions', route: '/models/1/versions', pageType: 'list', states: LIST_STATES },

  // === datasets ===
  { module: 'datasets', pageName: 'dataset-list', route: '/datasets', pageType: 'list', states: LIST_STATES },
  { module: 'datasets', pageName: 'dataset-create', route: '/datasets/create', pageType: 'form', states: ['default'] },
  { module: 'datasets', pageName: 'dataset-detail', route: '/datasets/1', pageType: 'detail', states: DETAIL_STATES },
  { module: 'datasets', pageName: 'dataset-versions', route: '/datasets/1/versions', pageType: 'list', states: LIST_STATES },

  // === resource-quotas ===
  { module: 'resource-quotas', pageName: 'resource-quotas', route: '/resource-quotas', pageType: 'list', states: LIST_STATES },

  // === spaces ===
  { module: 'spaces', pageName: 'space-list', route: '/spaces', pageType: 'list', states: LIST_STATES },
  { module: 'spaces', pageName: 'space-create', route: '/spaces/create', pageType: 'form', states: ['default'] },
  { module: 'spaces', pageName: 'ide', route: '/ide', pageType: 'special', states: ['default'] },

  // === monitoring ===
  { module: 'monitoring', pageName: 'monitoring', route: '/monitoring', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === audit ===
  { module: 'audit', pageName: 'audit-logs', route: '/audit-logs', pageType: 'list', states: LIST_STATES },

  // === admin ===
  { module: 'admin', pageName: 'admin-home', route: '/admin', pageType: 'dashboard', states: ['default'] },
  { module: 'admin', pageName: 'user-management', route: '/admin/users', pageType: 'list', states: LIST_STATES },

  // === reports ===
  { module: 'reports', pageName: 'reports-home', route: '/reports', pageType: 'dashboard', states: ['default'] },
  { module: 'reports', pageName: 'resource-usage', route: '/reports/resource-usage', pageType: 'dashboard', states: DASHBOARD_STATES },
  { module: 'reports', pageName: 'cost-analysis', route: '/reports/cost-analysis', pageType: 'dashboard', states: DASHBOARD_STATES },

  // === 错误页 ===
  { module: 'shared', pageName: 'not-found', route: '/404', pageType: 'special', states: ['default'], requiresAuth: false },
  { module: 'shared', pageName: 'unauthorized', route: '/unauthorized', pageType: 'special', states: ['default'], requiresAuth: false },
];

/** 预期截图总数 = Σ(states) × 2 主题 */
export const EXPECTED_SCREENSHOT_COUNT = AUDIT_PAGES.reduce((sum, p) => sum + p.states.length, 0) * 2;
```

- [ ] **Step 2: 语法验证（经 Playwright 收集器）**

主 tsconfig `include: ["src"]` 不含 e2e，tsc 单文件检查会脱离项目配置，因此用 Playwright 自身的转译收集来验证：

```bash
cd frontend && npx playwright test --project=audit --list 2>&1 | tail -2
```

Expected: 收集成功无报错（此时还没有 spec 引用 manifest，列出 0 个测试属正常；语法错误会在此暴露）。

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/audit/routes-manifest.ts
git commit -m "feat(frontend): 新增 UI 审计页面清单（28 页 × 状态豁免矩阵）"
```

---

### Task 3: 认证 Mock 与主题注入 auditSetup.ts

**Files:**
- Create: `frontend/e2e/audit/auditSetup.ts`

- [ ] **Step 1: 写入 auditSetup.ts（完整代码）**

```typescript
/**
 * 审计流水线基础设施：认证 Mock + 主题注入
 *
 * 完全脱离真实后端：mock 刷新/用户端点，注入 refresh token 触发应用静默续期。
 * 端点形状参照 src/features/auth/types/index.ts (TokenResponse/UserResponse)。
 */

import { Page } from '@playwright/test';

/** Mock 认证端点并注入登录态（admin 角色，保证可访问全部页面） */
export async function setupAuditAuth(page: Page) {
  await page.route('**/api/v1/auth/token/refresh', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'audit-access-token',
        refresh_token: 'audit-refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
      }),
    }),
  );

  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        display_name: '平台管理员',
        role: 'admin',
        status: 'active',
        auth_type: 'local',
      }),
    }),
  );

  await page.addInitScript(() => {
    sessionStorage.setItem('auth.refresh_token', 'audit-refresh-token');
  });
}

/** 注入主题偏好（zustand persist 格式，key 与 store/slices/uiSlice.ts 一致） */
export async function setTheme(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((t: string) => {
    localStorage.setItem(
      'ui-storage',
      JSON.stringify({
        state: { sidebarOpen: true, theme: t, density: 'comfortable' },
        version: 0,
      }),
    );
  }, theme);
}
```

- [ ] **Step 2: 核对三处契约（防止静默失效）**

逐一确认，若不一致以源码为准修正 auditSetup.ts：

```bash
cd frontend
grep -n "auth.refresh_token" src/features/auth -r          # sessionStorage key
grep -rn "role" src/app/router/guards/RoleGuard.tsx | head # admin 角色判定值
grep -n "version" src/store/slices/uiSlice.ts              # persist version（若显式声明）
```

Expected: key 为 `auth.refresh_token`；RoleGuard 接受 `'admin'`；persist 未显式声明 version（默认 0）或与注入值一致。

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/audit/auditSetup.ts
git commit -m "feat(frontend): 审计流水线认证 Mock 与主题注入工具"
```

---

### Task 4: 状态切换 Mock 引擎 auditMockApi.ts

**Files:**
- Create: `frontend/e2e/audit/auditMockApi.ts`

- [ ] **Step 1: 写入 auditMockApi.ts（完整代码）**

```typescript
/**
 * 审计状态 Mock 引擎
 *
 * 注册顺序约定（Playwright 后注册者优先匹配）：
 *   1. 兜底 catch-all（最先注册，最低优先级）
 *   2. extras（页面依赖的次要 API）
 *   3. primary（主数据 API，按状态切换）
 * 认证 mock 在 setupAuditAuth 中注册（晚于 catch-all 即可生效）。
 */

import { Page } from '@playwright/test';
import { AuditState, PageSpec } from './routes-manifest';

const EMPTY_LIST = { items: [], total: 0, page: 1, page_size: 20 };

function json(body: unknown, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

/** 兜底：未声明的 GET API 返回空列表形状，避免页面因未 mock 的请求而崩溃 */
export async function setupCatchAll(page: Page) {
  await page.route('**/api/v1/**', (route, request) => {
    if (request.method() !== 'GET') return route.fallback();
    return route.fulfill(json(EMPTY_LIST));
  });
}

/** 按页面声明与目标状态注册 mock */
export async function setupStateMocks(page: Page, spec: PageSpec, state: AuditState) {
  for (const extra of spec.extras ?? []) {
    await page.route(extra.pattern, (route, request) => {
      if (request.method() !== 'GET') return route.fallback();
      return route.fulfill(json(extra.defaultBody));
    });
  }

  if (!spec.primary) return;
  const primary = spec.primary;

  await page.route(primary.pattern, (route, request) => {
    if (request.method() !== 'GET') return route.fallback();
    switch (state) {
      case 'default':
        return route.fulfill(json(primary.defaultBody));
      case 'empty':
        return route.fulfill(json(primary.emptyBody ?? EMPTY_LIST));
      case 'error':
        // 详情页用 404（spec §5.4），其余用 500
        return spec.pageType === 'detail'
          ? route.fulfill(json({ detail: '资源不存在' }, 404))
          : route.fulfill(json({ detail: '服务器内部错误' }, 500));
      case 'loading':
        // 永不返回，页面停留在加载态
        return new Promise<void>(() => {});
    }
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/e2e/audit/auditMockApi.ts
git commit -m "feat(frontend): 审计状态 Mock 引擎（四态切换 + 兜底拦截）"
```

---

### Task 5: 截图流水线主程序 + training 模块冒烟

**Files:**
- Create: `frontend/e2e/audit/screenshot-pipeline.spec.ts`
- Modify: `frontend/e2e/audit/routes-manifest.ts`（为 training 4 页补 primary，复用现有 fixtures）

- [ ] **Step 1: 写入流水线主程序（完整代码）**

```typescript
/**
 * UI/UX 审计截图流水线
 *
 * 运行：npm run audit:screens
 * 过滤单模块：npm run audit:screens -- --grep "training/"
 * 产出：e2e/audit/audit-output/<日期>/<module>/<page>--<state>--<theme>.png
 */

import { test } from '@playwright/test';
import { AUDIT_PAGES } from './routes-manifest';
import { setupAuditAuth, setTheme } from './auditSetup';
import { setupCatchAll, setupStateMocks } from './auditMockApi';

const THEMES = ['light', 'dark'] as const;
const RUN_DATE = process.env.AUDIT_DATE || new Date().toISOString().slice(0, 10);

for (const spec of AUDIT_PAGES) {
  for (const state of spec.states) {
    for (const theme of THEMES) {
      test(`${spec.module}/${spec.pageName} [${state}] [${theme}]`, async ({ page }) => {
        // 注册顺序：catch-all → 主题/认证 → 页面 mock（后注册优先）
        await setupCatchAll(page);
        await setTheme(page, theme);
        if (spec.requiresAuth !== false) {
          await setupAuditAuth(page);
        }
        await setupStateMocks(page, spec, state);

        await page.goto(spec.route);

        if (state === 'loading') {
          // 主 API 永不返回，等待加载指示渲染稳定
          await page.waitForTimeout(1500);
        } else {
          await page.waitForLoadState('networkidle');
          await page.waitForTimeout(500); // 等待图表/动画静止
        }

        await page.screenshot({
          path: `e2e/audit/audit-output/${RUN_DATE}/${spec.module}/${spec.pageName}--${state}--${theme}.png`,
          fullPage: true,
        });
      });
    }
  }
}
```

- [ ] **Step 2: 为 training 模块补全 primary（manifest 修改）**

读取 `frontend/e2e/fixtures/trainingJobs.ts` 的导出（`mockTrainingJobs`、`getMockTrainingJobDetail`、`createPaginatedResponse`），在 manifest 顶部 import，并给 training 的 4 个 PageSpec 补上 `primary`：

```typescript
import { mockTrainingJobs, getMockTrainingJobDetail, createPaginatedResponse } from '../fixtures/trainingJobs';
```

```typescript
  // training-list
  primary: {
    pattern: /\/api\/v1\/training-jobs(\?.*)?$/,
    defaultBody: createPaginatedResponse(mockTrainingJobs, 1, 20),
  },
  // training-detail（pattern 排除子路径，参考 mockApi.ts:92 写法）
  primary: {
    pattern: /\/api\/v1\/training-jobs\/(\d+)$/,
    defaultBody: getMockTrainingJobDetail(1),
  },
  // checkpoints 列表页 primary 留待 Task 6（fixtures/checkpoints.ts）
  // training-create 是表单页，无 primary
```

注意：训练详情页有 checkpoints/metrics 等 Tab 子请求，由 catch-all 兜底返回空列表，default 截图主体信息仍完整；如详情页因兜底数据崩溃，把崩溃请求提为 `extras` 并给出合规形状。

- [ ] **Step 3: 冒烟运行 training 模块**

```bash
cd frontend && npm run audit:screens -- --grep "training/"
```

Expected: 共 **24** 个测试通过——`training-list` 8（4 态×2 主题）、`training-create` 2、`training-detail` 6、`checkpoints` 8（grep "training/" 同样匹配到它；其 primary 未配，default 态显示空表也算通过——本任务只验证管道通畅）。

- [ ] **Step 4: 人工核验截图质量**

用 Read 工具查看以下截图，确认：页面完整渲染（非白屏/登录页）、dark 主题真实生效、loading 态有加载指示、error 态有错误提示：

```
frontend/e2e/audit/audit-output/<日期>/training/training-list--default--light.png
frontend/e2e/audit/audit-output/<日期>/training/training-list--default--dark.png
frontend/e2e/audit/audit-output/<日期>/training/training-list--loading--light.png
frontend/e2e/audit/audit-output/<日期>/training/training-list--error--light.png
```

若截到登录页 = auth 注入失效，回查 Task 3 Step 2 的三处契约。

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/audit/screenshot-pipeline.spec.ts frontend/e2e/audit/routes-manifest.ts
git commit -m "feat(frontend): 审计截图流水线主程序 + training 模块冒烟通过"
```

---

### Task 6: 补全缺失模块的 fixtures（datasets/models/templates/auditLogs/users/checkpoints）

**Files:**
- Create: `frontend/e2e/audit/fixtures/datasets.ts`
- Create: `frontend/e2e/audit/fixtures/models.ts`
- Create: `frontend/e2e/audit/fixtures/templates.ts`
- Create: `frontend/e2e/audit/fixtures/auditLogs.ts`
- Create: `frontend/e2e/audit/fixtures/users.ts`
- Create: `frontend/e2e/audit/fixtures/checkpoints.ts`
- Modify: `frontend/e2e/audit/routes-manifest.ts`（补全对应 primary）

**Fixture 编写规约**（每个文件遵守）：
1. **形状以模块类型定义为唯一依据**：逐字段对照 `frontend/src/features/<module>/types/index.ts` 的 `{Entity}Summary`/`{Entity}Detail`，不要凭记忆编字段
2. **API 路径以模块 api 层为唯一依据**：查 `frontend/src/features/<module>/api/*Api.ts` 里的实际请求路径（如 `/datasets`、`/models/{id}/versions`），manifest 的 pattern 必须与之匹配
3. 纯对象、不 import `src/`（与现有 e2e/fixtures 约定一致）
4. default 数据 6-8 条、状态/类型多样化、名称描述用真实感中文（如"通用大模型预训练语料-v2"），让 default 截图接近真实使用密度
5. 详情页 fixture 单独导出（含 Detail 扩展字段）

- [ ] **Step 1: 写 datasets fixture（完整示例，其余模块照此模式）**

`frontend/e2e/audit/fixtures/datasets.ts`（字段对照 `src/features/datasets/types/index.ts` 的 `DatasetSummary`/`DatasetDetail`）：

```typescript
/**
 * 审计用数据集 fixture
 * 形状对照: src/features/datasets/types/index.ts (DatasetSummary / DatasetDetail)
 */

const base = {
  visibility: 'private' as const,
  owner_id: 1,
  owner_username: 'admin',
  tags: null,
  last_accessed_at: '2026-06-10T08:30:00Z',
};

export const mockDatasets = [
  { ...base, id: 1, name: '通用大模型预训练语料-v2', description: 'CommonCrawl 清洗后中英混合语料，约 1.2TB', version: 'v2.1.0', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2', total_size_bytes: 1319413953331, file_count: 18420, dataset_type: 'text', data_format: 'jsonl', status: 'available', tags: ['预训练', 'NLP'], created_at: '2026-03-02T10:00:00Z', updated_at: '2026-05-28T09:12:00Z' },
  { ...base, id: 2, name: '指令微调数据集-中文客服', description: '客服对话指令微调样本 48 万条', version: 'v1.4.2', storage_type: 's3', storage_uri: 's3://ai-studio-data/sft/customer-service', total_size_bytes: 2147483648, file_count: 12, dataset_type: 'text', data_format: 'parquet', status: 'available', tags: ['SFT'], created_at: '2026-04-11T06:20:00Z', updated_at: '2026-06-01T11:00:00Z' },
  { ...base, id: 3, name: '工业质检图像集', description: '产线缺陷检测标注图像', version: 'v3.0.0', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/qc-images', total_size_bytes: 549755813888, file_count: 230400, dataset_type: 'image', data_format: 'coco', status: 'preparing', tags: ['CV', '质检'], created_at: '2026-05-19T02:00:00Z', updated_at: '2026-06-11T15:45:00Z' },
  { ...base, id: 4, name: '语音指令音频库', description: '智能家居唤醒词与指令音频', version: 'v1.0.0', storage_type: 's3', storage_uri: 's3://ai-studio-data/audio/voice-cmd', total_size_bytes: 107374182400, file_count: 96000, dataset_type: 'audio', data_format: 'wav', status: 'available', tags: ['语音'], created_at: '2026-02-25T09:00:00Z', updated_at: '2026-04-30T10:10:00Z' },
  { ...base, id: 5, name: '推荐系统行为日志', description: '匿名化用户行为序列，用于排序模型训练', version: 'v0.9.1', storage_type: 'efs', storage_uri: 'efs://fs-77aa/datasets/rec-logs', total_size_bytes: 3298534883328, file_count: 412, dataset_type: 'tabular', data_format: 'parquet', status: 'archived', tags: ['推荐'], created_at: '2025-12-01T00:00:00Z', updated_at: '2026-01-15T08:00:00Z' },
  { ...base, id: 6, name: '多模态对齐数据-图文对', description: 'LAION 子集精洗图文对', version: 'v2.0.0-beta', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/mm-pairs', total_size_bytes: 879609302220, file_count: 5120000, dataset_type: 'custom', data_format: 'webdataset', status: 'error', tags: ['多模态'], created_at: '2026-05-30T13:00:00Z', updated_at: '2026-06-12T01:20:00Z' },
];

export const datasetListResponse = {
  items: mockDatasets,
  total: mockDatasets.length,
  page: 1,
  page_size: 20,
};

export const datasetDetailResponse = {
  ...mockDatasets[0],
  training_jobs_count: 3,
};

/** 版本列表：形状对照 src/features/datasets/types 中版本相关类型（编写时核对） */
export const datasetVersionsResponse = {
  items: [
    { id: 11, dataset_id: 1, version: 'v2.1.0', change_note: '增量清洗：去重率提升至 99.2%', size_bytes: 1319413953331, created_at: '2026-05-28T09:12:00Z' },
    { id: 10, dataset_id: 1, version: 'v2.0.0', change_note: '全量重建：合并英文语料', size_bytes: 1209462790554, created_at: '2026-04-02T10:00:00Z' },
    { id: 9, dataset_id: 1, version: 'v1.0.0', change_note: '初始版本', size_bytes: 858993459200, created_at: '2026-03-02T10:00:00Z' },
  ],
  total: 3,
  page: 1,
  page_size: 20,
};
```

**注意**：上述版本类型字段是占位示例——编写时必须打开 `src/features/datasets/types/index.ts` 核对版本实体真实字段后修正。

- [ ] **Step 2: 照同样规约写其余 5 个 fixture**

每个文件动手前先读两处（字段与路径的唯一真实源）：

| fixture | 类型定义 | API 层 |
|---------|---------|--------|
| `models.ts` | `src/features/models/types/index.ts` | `src/features/models/api/` |
| `templates.ts` | `src/features/templates/types/index.ts` | `src/features/templates/api/` |
| `auditLogs.ts` | `src/features/audit/types/index.ts` | `src/features/audit/api/` |
| `users.ts` | `src/features/admin/types/index.ts` | `src/features/admin/api/` |
| `checkpoints.ts` | `src/features/training/types/index.ts`（Checkpoint 相关） | `src/features/training/api/` |

- [ ] **Step 3: manifest 补全 6 个模块相关页面的 primary**

按各模块 api 层确认的真实路径写 pattern（列表页注意用 `$` 锚定避免吞掉详情路径，参考 mockApi.ts 的正则）。涉及页面：dataset-list/detail/versions、model-list/detail/versions、template-list/detail、audit-logs、user-management、checkpoints。

- [ ] **Step 4: 运行受影响模块截图验证**

```bash
cd frontend && npm run audit:screens -- --grep "(datasets|models|templates|audit|admin|training/checkpoints)"
```

Expected: 全部通过。用 Read 抽看 `dataset-list--default--light.png` 与 `user-management--default--light.png`，确认表格有真实感数据而非空表。

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/audit/fixtures/ frontend/e2e/audit/routes-manifest.ts
git commit -m "feat(frontend): 审计 fixtures 补全六模块真实感数据"
```

---

### Task 7: 全量流水线跑通（dashboard/monitoring/reports/spaces/quotas 等收尾）

**Files:**
- Modify: `frontend/e2e/audit/routes-manifest.ts`（补全剩余页面的 primary/extras）
- Modify: `frontend/e2e/audit/fixtures/`（按需新增 dashboard/monitoring/reports 的指标类 fixture）

- [ ] **Step 1: 排查剩余页面的主数据 API**

dashboard（HomePage）、monitoring、reports 三页、spaces 两页、resource-quotas、IDE 页，逐一查 api 层确定端点：

```bash
cd frontend
grep -rn "apiClient\.\(get\|post\)" src/features/dashboard/api/ src/features/monitoring/api/ src/features/reports/api/ src/features/spaces/api/ src/features/resource-quotas/api/ 2>/dev/null | grep -v test
```

spaces/resource-quotas 优先复用 `e2e/fixtures/{spaces,resourceQuotas}.ts` 既有数据。指标/图表类端点新建 `fixtures/metrics.ts` 集中存放（数值要有起伏，让图表截图真实）。

**重点核对数组型响应**：monitoring/reports 的多个端点返回**数组**而非 `{items,...}` 对象（如 `/monitoring/metrics` → `MetricSeries[]`），catch-all 兜底的列表形状会让图表组件 `.map` 崩溃——这些端点必须逐一声明为 `primary`/`extras` 并按 api 层真实返回类型给 fixture。

- [ ] **Step 2: 全量运行**

```bash
cd frontend && npm run audit:screens 2>&1 | tail -5
```

Expected: 全部测试通过（28 页对应的 `EXPECTED_SCREENSHOT_COUNT` 个截图任务）。

- [ ] **Step 3: 数量与完整性校验**

```bash
cd frontend
npx playwright test --project=audit --list 2>&1 | tail -1
find e2e/audit/audit-output/$(date +%Y-%m-%d) -name '*.png' | wc -l
```

Expected: 两个数字一致（test 总数 = PNG 总数），且与 manifest 的 `EXPECTED_SCREENSHOT_COUNT` 相等。

- [ ] **Step 4: 抽样核验 6 张关键截图**

用 Read 查看：`home--default--light/dark`、`monitoring--default--light`、`space-list--default--light`、`login--default--dark`、`not-found--default--light`。确认无白屏、无登录页误截、dark 模式生效。

- [ ] **Step 5: 既有测试回归**

```bash
cd frontend && npm run lint && npx tsc --noEmit && npm test -- --run 2>&1 | tail -3
```

Expected: lint 0 警告、类型检查通过、单元测试全绿（审计代码不触碰 src/，理论上零影响，跑一遍确认）。

- [ ] **Step 6: Commit**

```bash
git add frontend/e2e/audit/
git commit -m "feat(frontend): 审计截图流水线全量跑通（28 页 × 状态 × 双主题）"
```

---

### Task 8: design-reviewer agent

**Files:**
- Create: `.claude/agents/design-reviewer.md`（仓库根 `.claude/`，需新建 agents 目录）

- [ ] **Step 1: 写入 agent 定义（完整内容）**

````markdown
---
name: design-reviewer
description: UI/UX 设计质量评审专家。对前端页面截图按四维度评分框架（信息架构/交互完整度/一致性/视觉品质）独立打分并输出结构化报告。在 /ui-audit、/ui-fix 流程中被委派执行评分环节。评分必须由本 agent 在独立上下文完成，写代码的上下文不得给自己打分。
tools: Read, Glob, Grep
---

你是企业级 SaaS 产品的资深 UI/UX 设计评审专家，参照 Databricks、Weights & Biases、Vertex AI 等标杆 ML 平台的商用水准评审页面截图。

## 评分框架（来源：docs/superpowers/specs/2026-06-12-ui-ux-quality-system-design.md §3.2）

对每个页面（该页面的全部状态 × 双主题截图合并为一个评审单元）按四维度打分（1-5，允许 0.5 步进）：

| 维度 | 权重 | 评分要点 |
|------|------|---------|
| 信息架构 IA | 30% | 信息层级清晰度、扫描效率、主次操作区分、关键信息可达性 |
| 交互完整度 IX | 30% | 四态完备（loading/empty/error/default）、操作反馈可见性、表单体验、引导与帮助文案 |
| 一致性 CONS | 25% | 与同类页面模式统一（列表/详情/表单/Dashboard）、术语与文案一致、组件用法一致 |
| 视觉品质 VIS | 15% | 间距节奏、对齐、暗色模式无瑕疵、整体专业感 |

**评分锚点**（强制对照，给分必须引用锚点理由）：
- 5 = 可直接对外演示给客户，与 Databricks/W&B 同屏不违和
- 4 = 商用可接受，有可挑剔的小瑕疵
- 3 = 内部工具水准，功能完整但体验生硬
- 2 = 有明显缺陷（状态缺失、布局混乱）
- 1 = 不可用或严重破损

**综合分** = 30%×IA + 30%×IX + 25%×CONS + 15%×VIS，保留一位小数。商用门槛 4.0。

## 问题分级

- **P0**: 破坏可用性或可信度（错误状态白屏、数据不可读、暗色模式文字不可见）
- **P1**: 明显不专业（空状态只有一行字、无操作引导、布局失衡、术语不一致）
- **P2**: 打磨项（间距不齐、文案可更精炼、次要视觉瑕疵）

## 评审流程

1. 用 Glob 列出指定目录下该模块的全部截图
2. 用 Read 逐张查看（注意成对比较 light/dark、对照同模块各状态）
3. 跨页面横向对照：同为列表页的页面之间模式是否一致
4. 输出下方格式的报告（仅输出报告，不写文件、不改代码）

## 输出格式（严格遵守，便于上游聚合）

```markdown
## 模块: <module>

### 页面: <pageName>
- IA: <分> — <一句话理由，引用锚点>
- IX: <分> — <理由（必须提及四态各自的表现）>
- CONS: <分> — <理由>
- VIS: <分> — <理由（必须提及暗色模式）>
- **综合: <加权分>**

**问题清单**:
- [P0|P1|P2] [<维度>] <问题描述> （截图: <文件名>）

（…每页一节…）

### 模块小结
- 模块均分: <分>
- 最高频问题模式: <归纳>
```

## 评审纪律

- 证据优先：每个问题必须指明所在截图文件名
- 不脑补：截图未覆盖的交互（hover、动画）不评、不猜
- 锚点强制：给 4 分以上必须能回答"为什么能对外演示"；给 3 分以下必须指出具体的生硬之处
- 独立性：不接受任何"这页已经改进过"之类的上下文暗示影响打分
````

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/design-reviewer.md
git commit -m "feat(claude): design-reviewer 设计评审 agent（四维度独立评分）"
```

---

### Task 9: /ui-audit skill

**Files:**
- Create: `.claude/skills/ui-audit/SKILL.md`

- [ ] **Step 1: 写入 skill（完整内容）**

````markdown
---
name: ui-audit
description: 对前端页面执行 UI/UX 审计：运行截图流水线，委派 design-reviewer agent 四维度评分，聚合产出审计报告三件套。用法：/ui-audit [模块名|all]。适用于基线审计和批次修复后的回归审计。
---

# UI/UX 审计

对指定模块（或全部有页面的模块，12 业务模块 + dashboard，billing 无独立页面除外）执行"截图 → 独立评分 → 聚合报告"闭环。

## 参数

- `all`：全量审计（基线或全量回归）
- `<module>`：单模块审计（如 `training`），用于批次修复后的回归

## 流程

### 1. 运行截图流水线

```bash
cd frontend && npm run audit:screens            # all
cd frontend && npm run audit:screens -- --grep "<module>/"   # 单模块
```

确认输出目录 `frontend/e2e/audit/audit-output/<今日日期>/` 下 PNG 数量与测试数一致。失败的截图任务必须修复后重跑，不允许带着缺图评分。

### 2. 委派评分（每模块一次 Agent 调用）

对每个待审模块，用 Agent 工具派发 `design-reviewer` agent，prompt 提供：
- 截图目录绝对路径：`frontend/e2e/audit/audit-output/<日期>/<module>/`
- 该模块在 `frontend/e2e/audit/routes-manifest.ts` 中的页面清单（pageName、pageType、states）
- 指令：按其内置评分框架输出结构化报告

多模块时可并行派发（互相独立）。收集各模块返回的报告文本。

### 3. 聚合报告三件套

写入 `frontend/docs/audit/<日期>-<场景>/`（场景：`baseline` 或 `batch-N-regression`）：

**`score-matrix.md`** — 模块 × 4 维度评分矩阵（12 个有页面的模块 + dashboard；billing 无独立页面，矩阵末尾单独标注"billing: 无路由页面，不参与评分"）：
```markdown
| 模块 | 页面 | IA | IX | CONS | VIS | 综合 | 达标(≥4.0) |
|------|------|----|----|------|-----|------|-----------|
```
末尾给出：全局均分、达标率、最低分页面 Top 5。

**`findings.md`** — 问题清单，按严重度分组（P0 → P1 → P2），每条含：模块/页面、维度、描述、截图文件名。给每条分配稳定编号（如 `F-001`），供修复任务引用。

**`audit-report.md`** — 总报告：
- 执行摘要（全局均分、P0/P1/P2 计数、与上次审计对比——如有）
- 高频问题模式 Top 5（跨模块归纳，这是阶段 2 规范的内容优先级输入）
- 各模块一段式小结
- 修复批次建议（按 spec §7 的预设批次，结合实际评分微调）

### 4. 汇报

向用户输出：全局均分、达标率、P0 数量、报告文件路径。回归场景额外输出与基线的分数对比。

## 纪律

- 评分一律出自 design-reviewer agent，本上下文不打分、不改分
- 报告如实记录，包括 0 分页面和流水线缺陷
- 审计中发现的后端 API 缺口记入 findings（标注"移交后端"），不在前端绕过
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/ui-audit/SKILL.md
git commit -m "feat(claude): /ui-audit 审计编排 skill"
```

---

### Task 10: 执行基线审计（阶段 1）

**Files:**
- Create: `frontend/docs/audit/<日期>-baseline/audit-report.md`
- Create: `frontend/docs/audit/<日期>-baseline/findings.md`
- Create: `frontend/docs/audit/<日期>-baseline/score-matrix.md`

- [ ] **Step 1: 按 /ui-audit skill 的流程执行 `all` 审计**

严格按 `.claude/skills/ui-audit/SKILL.md` 步骤：重跑全量截图（确保最新）→ 13 个模块并行派发 design-reviewer（每模块一个 Agent 调用，附截图目录与页面清单）→ 收集 13 份报告。

- [ ] **Step 2: 聚合三件套**

按 skill 中的模板写入 `frontend/docs/audit/<日期>-baseline/` 三个文件。重点核对：
- score-matrix 行数 = 28 页
- findings 每条都有截图文件名与稳定编号
- audit-report 的"高频问题模式 Top 5"有跨模块证据支撑（这是阶段 2 规范的直接输入）

- [ ] **Step 3: Commit**

```bash
git add frontend/docs/audit/
git commit -m "docs(frontend): UI/UX 基线审计报告（13 模块 28 页四维度评分）"
```

- [ ] **Step 4: 向用户汇报基线结论**

输出：全局均分、达标率、P0/P1/P2 计数、最低分 Top 5 页面、高频问题模式 Top 5、报告路径。并说明下一步：基于审计报告制定阶段 2（靶向规范）计划。

---

## 验收清单（计划级 DoD）

- [ ] `npm run audit:screens` 一条命令产出全部截图，数量与 manifest 的 `EXPECTED_SCREENSHOT_COUNT` 一致
- [ ] `npm run test:e2e` 不再包含 audit 测试（project 隔离生效）
- [ ] `npm run lint`、`npx tsc --noEmit`、`npm test -- --run` 全绿
- [ ] design-reviewer agent 与 /ui-audit skill 落盘并在基线审计中实际使用
- [ ] 基线审计三件套提交，28 页全部有四维度评分与综合分
- [ ] 用户收到基线结论汇报

## 不在本计划内（后续计划）

- 阶段 2：四份设计规范（依赖基线审计的高频问题模式）
- 阶段 3：/ui-fix skill、rules 增强（依赖阶段 2 规范）
- 阶段 4：三批次修复（依赖以上全部）
