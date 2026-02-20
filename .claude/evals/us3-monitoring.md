## EVAL: us3-monitoring
Created: 2026-02-20
Module: backend/src/modules/monitoring/ + frontend/src/features/monitoring/
Phase: 5 (P1 Must-Have)
Tasks: T053-T054, T061-T063, T066-T068, T220-T221

### Capability Evals

#### 后端 API
- [ ] GET /monitoring/metrics 返回 Prometheus 指标 (GPU 利用率、集群容量、任务队列长度)
- [ ] GET /monitoring/metrics 支持时间范围过滤
- [ ] 监控数据刷新频率 <= 30 秒

#### 集群监控服务
- [ ] HyperPodCluster 模型正确存储集群状态和容量信息
- [ ] 集群健康检查服务每 1 分钟执行一次
- [ ] 集群状态变更正确更新 hyperpod_clusters 表
- [ ] 集群健康降级 (degraded/unhealthy) 时触发告警

#### Prometheus 集成
- [ ] PrometheusService 正确查询 HyperPod Observability Add-on 指标
- [ ] 存储容量监控: 80% 警告告警正确触发
- [ ] 存储容量监控: 90% 严重告警正确触发并暂停检查点创建
- [ ] 存储容量监控: 95% 满载告警正确触发并暂停新任务提交
- [ ] StorageCapacityGuard 在 95% 使用率时正确拒绝新任务提交
- [ ] 网络性能监控: EFA 延迟 >10ms 时触发告警
- [ ] 网络性能监控: 带宽利用率 <80% 时触发告警

#### 训练指标服务 (T220)
- [ ] 训练指标查询服务正确查询 Prometheus query_range API
- [ ] 支持 Loss, Accuracy, Learning Rate, Throughput 指标
- [ ] 支持 avg/max/min/last 聚合函数
- [ ] 已完成任务的指标数据缓存 1 小时
- [ ] 训练指标查询延迟 <2 秒

#### Grafana 仪表盘
- [ ] Grafana dashboard JSON 配置正确定义集群健康面板
- [ ] Grafana dashboard 展示资源利用率和训练任务分布

#### 前端页面
- [ ] 集群监控仪表盘页面正确嵌入 Grafana iframe
- [ ] 实时指标图表组件 (MetricsCharts) 渲染折线图/柱状图/饼图
- [ ] 训练指标图表 (TrainingMetricsChart) 正确渲染 Loss/Accuracy 曲线
- [ ] 训练指标图表支持多任务叠加对比
- [ ] 训练指标图表运行中任务 30 秒自动刷新

### Regression Evals
- [ ] Prometheus 查询失败时返回缓存数据或明确错误
- [ ] 监控数据查询不影响训练任务性能
- [ ] 认证和权限检查正确应用于监控 API
- [ ] Prometheus 指标保留期 >= 30 天

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- FR-013: 集群监控刷新频率 <= 30 秒
- FR-020: 存储容量告警触发准确率 100%
- FR-021: 网络延迟 P99 <10ms
- FR-026: 训练指标查询延迟 <2 秒
- SC-008: Prometheus 指标保留期 >= 30 天
