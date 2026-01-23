# AI 训练平台前端设计规范

> **快速参考指南** - 完整视觉规范、页面模板、国际化、无障碍请查阅 `specs/frontend-design-guide.md`

---

## 一、核心设计原则

| 原则 | 要点 | 实践 |
|------|------|------|
| **效率优先** | 关键操作 ≤3 秒可达 | 首页快速入口、智能默认值、批量操作 |
| **渐进复杂** | 三层用户路径 | 模板→配置→自定义/YAML |
| **一致可信** | 操作可预测、可撤销 | 统一反馈模式、危险操作二次确认 |
| **Cloudscape First** | 禁止自定义样式覆盖 | 仅使用 Cloudscape 组件和变量 |

---

## 二、组件选择指南

| 场景 | 推荐组件 | 备选 |
|------|---------|------|
| 主操作 | `<Button variant="primary">` | - |
| 次要操作 | `<Button>` | `<Button variant="link">` |
| 状态展示 | `<StatusIndicator>` | `<Badge>` |
| 数据表格 | `<Table>` | `<Cards>` |
| 详情展示 | `<KeyValuePairs>` | `<ColumnLayout>` |
| 表单容器 | `<Form>` + `<Container>` | - |
| 分步流程 | `<Wizard>` | - |
| 通知消息 | `<Flashbar>` | - |
| 确认弹窗 | `<Modal>` | - |
| 侧边详情 | `<SplitPanel>` | `<Drawer>` |

---

## 三、状态反馈规范

### 操作反馈时效

| 操作类型 | 时效要求 | 反馈方式 |
|---------|---------|---------|
| 按钮点击 | 即时 | Loading 状态 |
| 表单提交 | ≤100ms | Spinner + 禁用按钮 |
| API 请求 | ≤3s | 进度指示器 |
| 后台任务 | 完成通知 | Toast + 通知中心 |

### 反馈组件示例

```tsx
// 成功
<Flashbar items={[{ type: "success", content: "任务创建成功" }]} />

// 错误（带重试）
<Flashbar items={[{
  type: "error",
  content: "创建失败",
  action: <Button>重试</Button>
}]} />

// 加载状态
<StatusIndicator type="loading">正在提交...</StatusIndicator>
```

---

## 四、禁止事项

| ❌ 禁止 | ✅ 正确做法 |
|--------|-----------|
| `style={{ backgroundColor: 'red' }}` | `<Button variant="primary">` |
| `<div style={{ marginTop: 20 }}>` | `<SpaceBetween size="m">` |
| `<input type="text" />` | `<Input value={v} onChange={h} />` |
| `import { LineChart } from 'recharts'` | `<LineChart />` (Cloudscape) |
| `style={{ backgroundColor: '#fff' }}` | `<Container variant="default">` |

---

## 五、危险操作确认

需要二次确认的操作：删除任务、停止运行任务、删除数据集、清空检查点、重置配额

```tsx
<Modal
  header="确认删除"
  footer={
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link">取消</Button>
      <Button variant="primary" disabled={confirmInput !== jobName}>
        确认删除
      </Button>
    </SpaceBetween>
  }
>
  <Alert type="warning">此操作不可撤销</Alert>
  <FormField label="请输入任务名称以确认">
    <Input value={confirmInput} onChange={e => setConfirmInput(e.detail.value)} />
  </FormField>
</Modal>
```

---

## 六、暗色模式

```tsx
import { applyMode, Mode } from '@cloudscape-design/global-styles';

const setTheme = (theme: 'light' | 'dark' | 'system') => {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyMode(isDark ? Mode.Dark : Mode.Light);
  } else {
    applyMode(theme === 'dark' ? Mode.Dark : Mode.Light);
  }
};
```

> 默认使用 Cloudscape 组件，自动适配暗色模式。禁止硬编码背景色或文字色。

---

## 七、提交前检查清单

### 页面必备

- [ ] 页面标题（Header 组件）
- [ ] 面包屑导航
- [ ] 主操作按钮（右上角）
- [ ] 加载/空/错误状态处理

### 表单必备

- [ ] 字段标签和提示
- [ ] 必填标记
- [ ] 实时验证 + 错误消息
- [ ] 提交确认

### 表格必备

- [ ] 排序 + 分页
- [ ] 列偏好设置
- [ ] 空/加载状态
- [ ] 行操作

### 代码质量

- [ ] TypeScript 严格模式通过
- [ ] ESLint 无警告
- [ ] 无自定义 CSS
- [ ] 全部使用 Cloudscape 组件
- [ ] 暗色模式下无显示异常

---

> **完整版文档**: `specs/frontend-design-guide.md` - 包含详细视觉规范、页面模板、色彩系统、间距系统、响应式设计、无障碍设计、国际化等。
