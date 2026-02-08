> **职责**: PR Review 检查清单的**单一真实源**，涵盖架构、Cloudscape 合规、安全、测试和性能检查项。

# PR Review 检查清单

---

## 分层与架构

- [ ] 新文件放置在正确的模块内分层 (types/api/hooks/components/pages)
- [ ] 依赖方向正确（只向下依赖）
- [ ] 没有跨 feature 的直接导入（通过 index.ts 或 EventBus）
- [ ] shared 层没有业务逻辑
- [ ] 每个模块有 `index.ts` 统一导出
- [ ] Types 层没有导入任何外部模块

详见 [architecture.md](architecture.md) §2-3

---

## 组件设计

- [ ] 组件类型正确（展示/容器/页面）
- [ ] Props 使用 interface 定义
- [ ] 事件处理函数命名以 `handle` 开头
- [ ] children 类型为 `React.ReactNode`
- [ ] 可选 Props 有合理默认值
- [ ] 复合组件使用 Context 共享状态

详见 [component-design.md](component-design.md) §1

---

## Cloudscape 合规

### 页面必备

- [ ] 页面标题（Header 组件）
- [ ] 面包屑导航
- [ ] 主操作按钮（右上角）
- [ ] 加载/空/错误状态处理

### 表单必备

- [ ] 字段标签和提示 (`<FormField>`)
- [ ] 必填标记
- [ ] 实时验证 + 错误消息
- [ ] 提交确认

### 表格必备

- [ ] 排序 + 分页
- [ ] 列偏好设置
- [ ] 空/加载状态
- [ ] 行操作

### 组件使用

- [ ] 全部使用 Cloudscape 组件（无自定义 CSS）
- [ ] 无内联样式 (`style={{}}`)
- [ ] 无原生 HTML 表单控件 (`<input>`, `<select>`)
- [ ] 间距使用 `<SpaceBetween>` 而非 margin/padding
- [ ] 暗色模式下无显示异常

详见 [component-design.md](component-design.md) §2

---

## 代码风格

- [ ] 命名符合规范 (PascalCase 组件, camelCase 函数, UPPER_SNAKE 常量)
- [ ] 没有 `any` 类型
- [ ] Props 使用 `interface` 定义
- [ ] 导入按规范排序 (React → 第三方 → 内部别名 → 相对 → 类型)
- [ ] 没有未使用的变量/导入

详见 [code-style.md](code-style.md) §0-2

---

## 状态管理

- [ ] 服务端数据使用 React Query
- [ ] 全局状态使用 Zustand
- [ ] Store 有 Selector Hooks 导出（细粒度订阅）
- [ ] Query Keys 使用 `@lib/query` 的 `queryKeys` 工厂
- [ ] 敏感数据不存入持久化 Store
- [ ] URL 相关状态使用 React Router searchParams

详见 [state-management.md](state-management.md) §0-2

---

## 安全

- [ ] 没有 `dangerouslySetInnerHTML` (除非必要且使用 DOMPurify)
- [ ] 没有 `eval()`, `new Function()`
- [ ] URL 跳转有验证（协议白名单）
- [ ] 用户输入有 Zod schema 验证
- [ ] 敏感数据不在 localStorage
- [ ] 没有硬编码的密钥
- [ ] 环境变量使用 `VITE_` 前缀

详见 [security.md](security.md) §0-4

---

## 测试

- [ ] 测试文件在 `tests/` 目录（镜像 src 结构）
- [ ] 使用可访问性查询（getByRole > getByLabelText > getByText > getByTestId）
- [ ] 异步操作正确等待 (`waitFor` / `findBy`)
- [ ] Mock 仅边界依赖（使用 MSW）
- [ ] 覆盖率达标 (≥80%)

详见 [testing.md](testing.md) §1-4

---

## 性能

- [ ] 路由级组件使用 `lazy()` 加载
- [ ] 大列表 (>100项) 使用虚拟列表
- [ ] `memo`/`useCallback`/`useMemo` 使用有明确理由
- [ ] 图片有 `loading="lazy"`
- [ ] 使用具名导入 (Tree Shaking)

详见 [performance.md](performance.md) §1-3

---

## 无障碍

- [ ] 图片有描述性 alt 文本
- [ ] 表单控件有关联的 label（Cloudscape `<FormField>`）
- [ ] 可交互元素可通过键盘访问
- [ ] 颜色对比度 >= 4.5:1
- [ ] 图标按钮有 `aria-label`
- [ ] 状态展示使用 `<StatusIndicator>`（颜色+图标+文字）

详见 [accessibility.md](accessibility.md) §1-4

---

## 项目结构

- [ ] 无临时文件被提交
- [ ] 环境变量已在 `.env.example` 声明
- [ ] TypeScript 严格模式通过 (`npx tsc --noEmit`)
- [ ] ESLint 无警告 (`npm run lint`)
