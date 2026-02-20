## EVAL: us5-spaces
Created: 2026-02-20
Last Check: 2026-02-20 (post-fix)
Module: backend/src/modules/spaces/ + frontend/src/features/spaces/
Phase: 7 (P2 Important)
Tasks: T081-T090

### Capability Evals

#### 后端 API
- [x] POST /ide/sessions 创建 SageMaker Space，返回 Studio URL
- [x] POST /ide/sessions 验证用户配额 (GPU/CPU/内存计入整体配额)
- [x] POST /ide/sessions 支持 ml.g5.xlarge (默认) 和 ml.g5.2xlarge 实例
- [x] GET /ide/sessions 支持分页、按 status 和 owner_id 过滤
- [x] GET /ide/sessions/{id} 返回详情，含 Studio URL、状态、资源使用
- [x] DELETE /ide/sessions/{id} 调用 DeleteSpace API 清理资源

#### SageMaker Spaces 集成
- [x] SageMaker Spaces 服务正确调用 HyperPod Space 模块 API
- [x] Space 创建成功后返回有效的 SageMaker Studio URL
- [x] 生命周期脚本 (Lifecycle Configuration) 预装 PyTorch/Transformers
- [x] EFS 持久化存储正确挂载
- [x] Space 状态同步服务每 30 秒同步一次 DescribeSpace 状态 (start_periodic_sync 已实现)
- [x] Space 状态转换正确 (pending -> running -> stopped -> deleted)

#### 性能要求
- [x] Space 启动时间 <3 分钟 (SLA 监控 + 超时告警已实现)
- [~] 并发启动 >= 50 个 Space 无错误 (无并发限制但缺负载测试)
- [x] 启动时间 P95/P99 统计通过 SpaceMetricsService 收集到 CloudWatch
- [x] 启动超时 >3 分钟正确触发 warning 告警

#### 镜像管理
- [x] 支持 Data Science、PyTorch、TensorFlow 官方镜像
- [x] 支持自定义镜像注册到 SageMaker Image Registry
- [x] 镜像版本管理正确执行

#### 前端页面
- [x] 开发空间创建页面支持选择 IDE 类型 (JupyterLab/VS Code)
- [x] 开发空间创建页面显示实例类型资源规格 (CPU/内存/GPU)
- [x] 开发空间创建页面显示启动进度和预估启动时间
- [x] 在线开发环境列表页面支持启动/停止/删除操作
- [x] IDE 嵌入组件 (IDEFrame) 正确嵌入 Studio URL，支持全屏

### Regression Evals
- [x] Space 创建不影响训练任务资源
- [x] Space 停止后 EFS 数据持久化保留
- [x] 认证和权限检查正确应用
- [x] 资源配额检查与训练任务共享统一配额池
- [x] 自动保存间隔: JupyterLab 120 秒、VS Code 1 秒

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- FR-023: IDE 启动时间 <3 分钟
- FR-024: 支持 >= 50 并发在线开发环境
