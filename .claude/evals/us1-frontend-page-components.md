## EVAL: us1-frontend-page-components
Created: 2026-01-25

### 概述

评估 US1 (P1) 训练任务管理的前端页面组件实现质量，覆盖任务 T032-T035e。

**涉及任务**:
- T032: 训练任务列表页面 (`TrainingJobListPage.tsx`)
- T033: 训练任务创建表单 (`CreateTrainingJobPage.tsx`, `TrainingJobForm.tsx`)
- T034: 训练任务详情页面 (`TrainingJobDetailPage.tsx`)
- T035: 训练状态监控组件 (`TrainingStatusMonitor.tsx`)
- T035a: 模型版本管理页面 (`ModelVersionsPage.tsx`)
- T035b: 模型列表页面 (`ModelListPage.tsx`)
- T035c: 模型详情页面 (`ModelDetailPage.tsx`)
- T035d: 模型列表组件 (`ModelTable.tsx`, `RegistrySyncStatus.tsx`)
- T035e: 模型版本对比组件 (`ModelVersionTable.tsx`, `ModelMetricsCompare.tsx`)

---

### Capability Evals (功能评估)

#### T032 - 训练任务列表页面
- [ ] C-T032-1: 页面使用 Cloudscape Table 组件展示训练任务列表
- [ ] C-T032-2: 支持分页功能 (切换页码正确加载数据)
- [ ] C-T032-3: 支持状态过滤 (submitted/running/paused/preempted/completed/failed)
- [ ] C-T032-4: 支持优先级过滤 (high/medium/low)
- [ ] C-T032-5: 实时状态更新 (30秒自动刷新或手动刷新按钮)
- [ ] C-T032-6: 点击任务行可跳转到详情页面
- [ ] C-T032-7: 提供创建训练任务按钮入口
- [ ] C-T032-8: API 层 `queries.ts` 正确定义 useTrainingJobs hook

#### T033 - 训练任务创建表单
- [ ] C-T033-1: 使用 Cloudscape Form 组件构建表单
- [ ] C-T033-2: 表单包含必填字段验证 (任务名称、实例类型、节点数)
- [ ] C-T033-3: 实例类型选择器显示可用选项 (p4d.24xlarge/p5.48xlarge/trn1.32xlarge)
- [ ] C-T033-4: 节点数输入支持数值验证 (范围限制)
- [ ] C-T033-5: 训练脚本路径验证 (S3 URI 格式)
- [ ] C-T033-6: 配额实时检查 (提交前验证资源可用性)
- [ ] C-T033-7: 提交成功后跳转到任务详情或列表页面
- [ ] C-T033-8: 提交失败显示明确的错误提示

#### T034 - 训练任务详情页面
- [ ] C-T034-1: 展示训练任务基本配置信息 (名称、实例类型、节点数、状态)
- [ ] C-T034-2: 展示实时训练指标 (通过 TrainingStatusMonitor 组件)
- [ ] C-T034-3: 展示检查点列表
- [ ] C-T034-4: 支持暂停操作 (仅 running 状态可见)
- [ ] C-T034-5: 支持恢复操作 (仅 paused 状态可见)
- [ ] C-T034-6: 支持终止操作 (非终态状态可见)
- [ ] C-T034-7: 展示训练日志流 (或提供日志查看入口)
- [ ] C-T034-8: 操作按钮状态与任务状态正确联动

#### T035 - 训练状态监控组件
- [ ] C-T035-1: 显示 GPU 利用率指标 (数值 + 状态指示器)
- [ ] C-T035-2: 显示训练进度 (Epoch/Step 进度条)
- [ ] C-T035-3: 显示 Loss 曲线 (使用 LineChart 组件)
- [ ] C-T035-4: 显示学习率曲线
- [ ] C-T035-5: 30秒刷新间隔 (running 状态时自动轮询)
- [ ] C-T035-6: 显示吞吐量指标 (samples/s)
- [ ] C-T035-7: 无数据时显示适当的空状态

#### T035a - 模型版本管理页面
- [ ] C-T035a-1: 使用 Cloudscape Table 展示模型版本历史
- [ ] C-T035a-2: 支持版本对比功能 (选择两个版本进行对比)
- [ ] C-T035a-3: 显示版本指标 (accuracy/loss)
- [ ] C-T035a-4: 显示 SageMaker Model Registry 同步状态
- [ ] C-T035a-5: 支持模型回滚操作入口
- [ ] C-T035a-6: 类型定义文件 `types/index.ts` 包含版本相关类型

#### T035b - 模型列表页面
- [ ] C-T035b-1: 使用 Cloudscape Table 组件展示模型列表
- [ ] C-T035b-2: 支持分页功能
- [ ] C-T035b-3: 支持状态过滤 (training/registered/deployed/archived)
- [ ] C-T035b-4: 支持 training_job_id 过滤
- [ ] C-T035b-5: 显示模型名称、版本数、Registry 同步状态
- [ ] C-T035b-6: 点击模型行可跳转到详情页面
- [ ] C-T035b-7: API 层 `modelApi.ts` 和 `queries.ts` 正确定义

#### T035c - 模型详情页面
- [ ] C-T035c-1: 展示模型元数据 (metrics, hyperparameters)
- [ ] C-T035c-2: 展示关联训练任务 (可点击跳转)
- [ ] C-T035c-3: 展示 Registry ARN
- [ ] C-T035c-4: 提供跳转至版本管理页面的入口

#### T035d - 模型列表组件
- [ ] C-T035d-1: ModelTable 复用 Cloudscape Table
- [ ] C-T035d-2: 支持行选择功能
- [ ] C-T035d-3: 支持批量操作 (如批量归档)
- [ ] C-T035d-4: RegistrySyncStatus 组件正确显示同步状态

#### T035e - 模型版本对比组件
- [ ] C-T035e-1: ModelVersionTable 展示版本历史表格
- [ ] C-T035e-2: ModelMetricsCompare 实现版本指标对比可视化
- [ ] C-T035e-3: 指标差异显示百分比变化
- [ ] C-T035e-4: 超参数变更高亮显示 (新增/修改/移除)
- [ ] C-T035e-5: hooks 文件 `useModel.ts` 和 `useModelVersions.ts` 正确定义

---

### Regression Evals (回归评估)

#### 通用质量标准
- [ ] R-001: 所有组件仅使用 @cloudscape-design/components (禁止自定义 CSS/MUI/Ant Design)
- [ ] R-002: 所有页面组件通过 `index.ts` 导出 (模块隔离)
- [ ] R-003: API 调用使用 TanStack Query (useQuery/useMutation)
- [ ] R-004: 类型定义完整 (无 any 类型逃逸)
- [ ] R-005: 错误状态有友好的用户提示
- [ ] R-006: 加载状态有 Loading 指示器
- [ ] R-007: 空状态有适当的占位提示
- [ ] R-008: 中文本地化 (界面文案使用中文)

#### 性能和可用性
- [ ] R-009: 列表页面首屏加载 < 3秒 (开发环境)
- [ ] R-010: 分页切换响应 < 1秒
- [ ] R-011: 过滤器操作响应流畅 (无卡顿)
- [ ] R-012: 图表组件渲染正常 (无报错)

#### 路由和导航
- [ ] R-013: /training-jobs 路由正确渲染列表页面
- [ ] R-014: /training-jobs/create 路由正确渲染创建页面
- [ ] R-015: /training-jobs/:id 路由正确渲染详情页面
- [ ] R-016: /models 路由正确渲染模型列表页面
- [ ] R-017: /models/:id 路由正确渲染模型详情页面
- [ ] R-018: /models/:id/versions 路由正确渲染版本管理页面

---

### Success Criteria (成功标准)

**Capability Evals**:
- pass@3 > 90% (3 次尝试中至少 90% 通过)

**Regression Evals**:
- pass^3 = 100% (连续 3 次必须 100% 通过)

---

### 验证方法

#### 自动化验证
```bash
# 1. 单元测试
npm test -- frontend/tests/unit/features/training
npm test -- frontend/tests/unit/features/models

# 2. 组件渲染测试
npm test -- --grep "TrainingJobListPage"
npm test -- --grep "ModelListPage"

# 3. E2E 测试 (如已配置)
npm run test:e2e -- --spec "training-jobs.spec.ts"
```

#### 手动验证清单
1. 启动前端开发服务器: `npm run dev`
2. 访问各页面路由检查渲染
3. 执行 CRUD 操作验证功能
4. 检查浏览器控制台无报错
5. 检查网络请求正确发送

---

### 文件清单

#### 训练任务模块 (`frontend/src/features/training/`)
- `pages/TrainingJobListPage.tsx`
- `pages/CreateTrainingJobPage.tsx`
- `pages/TrainingJobDetailPage.tsx`
- `components/TrainingJobTable.tsx`
- `components/TrainingJobForm.tsx`
- `components/TrainingStatusMonitor.tsx`
- `components/TrainingStatusBadge.tsx`
- `api/queries.ts`
- `api/trainingApi.ts` (或 `api/index.ts`)
- `types/index.ts`

#### 模型模块 (`frontend/src/features/models/`)
- `pages/ModelListPage.tsx`
- `pages/ModelDetailPage.tsx`
- `pages/ModelVersionsPage.tsx`
- `components/ModelTable.tsx`
- `components/ModelStatusBadge.tsx`
- `components/RegistrySyncStatus.tsx`
- `components/ModelVersionTable.tsx`
- `components/ModelMetricsCompare.tsx`
- `api/modelApi.ts`
- `api/queries.ts`
- `hooks/useModel.ts`
- `hooks/useModelVersions.ts`
- `types/index.ts`

---

### 备注

- 此评估基于 `tasks.md` 中 Phase 3 (US1) 前端页面组件任务定义
- 组件实现应遵循 `frontend/CLAUDE.md` 和 `frontend/DESIGN.md` 规范
- 所有组件必须符合 Cloudscape Design System 使用规范
