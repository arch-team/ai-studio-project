> **职责**: 性能规范 - 代码分割、Memoization、列表优化、Bundle 优化

# 性能规范 (Performance Standards)

---

## 0. 速查卡片

### 性能规则速查

| 场景 | 规则 |
|------|------|
| 路由级组件 | 必须 `lazy()` + `<Suspense>` |
| 列表 >100 项 | 使用 `react-window` 虚拟列表 |
| 传递给 memo 子组件的回调 | 使用 `useCallback` |
| 传递给 memo 子组件的对象 | 使用 `useMemo` |
| 昂贵计算 | 使用 `useMemo` |
| 导入第三方库 | 具名导入 (Tree Shaking) |

### 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| LCP | < 2.5s | 最大内容绘制 |
| INP | < 200ms | 交互到下次绘制 (已取代 FID，2024.03 起为 Core Web Vitals 正式指标) |
| CLS | < 0.1 | 累积布局偏移 |
| FCP | < 1.8s | 首次内容绘制 |
| TTI | < 3.8s | 可交互时间 |

---

## 1. 代码分割

### 1.1 路由级分割（必须）

```typescript
// app/router/routes.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

const TrainingListPage = lazy(() => import('@features/training/pages/TrainingListPage'));
const DatasetListPage = lazy(() => import('@features/datasets/pages/DatasetListPage'));
const ModelListPage = lazy(() => import('@features/models/pages/ModelListPage'));

export function AppRoutes() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/training" element={<TrainingListPage />} />
        <Route path="/datasets" element={<DatasetListPage />} />
        <Route path="/models" element={<ModelListPage />} />
      </Routes>
    </Suspense>
  );
}
```

### 1.2 其他分割规则

| 场景 | 方式 |
|------|------|
| 大型组件（编辑器、图表） | `lazy(() => import('./RichTextEditor'))` + `<Suspense>` |
| 预加载 | 鼠标悬停时 `import('@features/training/pages')` 触发预加载 |

---

## 2. Memoization

### ✅/❌ 示例

```typescript
// ✅ 需要 - 传递给 memo 子组件
function Parent() {
  const handleClick = useCallback(() => { /* ... */ }, []);
  const config = useMemo(() => ({ theme: 'dark' }), []);
  return <MemoizedChild onClick={handleClick} config={config} />;
}

// ✅ 需要 - 昂贵计算
function List({ items, filter }: Props) {
  const filtered = useMemo(
    () => items.filter(i => i.status === filter).sort((a, b) => a.name.localeCompare(b.name)),
    [items, filter]
  );
  return <ul>{filtered.map(/* ... */)}</ul>;
}

// ❌ 不需要 - 简单计算、不传给子组件
function Simple({ a, b }: Props) {
  const sum = a + b; // 不需要 useMemo
  const handleChange = (e: ChangeEvent) => { /* ... */ }; // 不需要 useCallback
  return <input onChange={handleChange} />;
}
```

---

## 3. 列表优化

### 规则

| 规则 | 说明 |
|------|------|
| 虚拟列表阈值 | >100 项使用 `react-window` (`FixedSizeList` + `AutoSizer`) |
| Key 必须稳定唯一 | ✅ `key={item.id}` / ❌ `key={index}`（列表会变化时） |

---

## 4. 状态优化

避免大对象状态导致不必要的重渲染。拆分 `useState` 和合理使用 Zustand Selector 是关键优化手段。

> 状态拆分最佳实践和 Zustand Selector 优化详见 [state-management.md](state-management.md) §2.3 和 §5

---

## 5. 图片优化

```tsx
// 原生懒加载 (推荐)
<img src={imageUrl} loading="lazy" alt="描述" />

// 响应式图片
<img
  src="/image.jpg"
  srcSet="/image-320.jpg 320w, /image-640.jpg 640w"
  sizes="(max-width: 320px) 280px, 600px"
  alt="描述"
  loading="lazy"
/>
```

> 注意: 本项目以 Cloudscape 组件为主，图片使用场景较少。如需展示图片，优先使用 Cloudscape 的 `<Box>` 容器包裹。

---

## 6. Bundle 优化

### Tree Shaking

```typescript
// ✅ 正确 - 具名导入 (可 tree shake)
import { debounce } from 'lodash-es';

// ❌ 错误 - 默认导入整个库
import _ from 'lodash';
```

**分析工具**: `rollup-plugin-visualizer` 可视化 bundle 组成
