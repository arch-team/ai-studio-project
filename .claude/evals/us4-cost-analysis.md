## EVAL: us4-cost-analysis
Created: 2026-02-20
Last Check: 2026-02-20
Module: backend/src/modules/billing/ + frontend/src/features/reports/
Phase: 6 (P2 Important)
Tasks: T069-T078

### Capability Evals

#### 成本计算服务
- [x] 成本计算引擎基于 instance_type + node_count + duration 正确计算训练成本
- [x] 支持多维度成本分析 (compute/storage/network)
- [x] AWS Cost Explorer 集成正确获取实际账单数据 (EC2, S3, FSx, EBS)
- [x] Cost Explorer 数据缓存策略 (1 小时刷新) 正确执行
- [x] 定价模型维护 HyperPod 实例定价表 (p4d/p5/trn1)
- [x] 定价模型包含 FSx、S3、网络传输成本计算
- [ ] 计算成本与 AWS Cost Explorer 实际账单误差率 <2% (CostAccuracyValidator 未集成到 API)

#### 资源使用聚合
- [x] 资源使用聚合支持按用户/项目分组
- [x] 资源使用聚合支持按时间维度分组 (day/week/month)
- [x] SQL aggregation 查询性能满足 <5 秒要求

#### 后端 API
- [x] GET /reports/resource-usage 返回 CPU/GPU/Storage 使用统计
- [x] GET /reports/resource-usage 支持时间范围和用户/项目过滤
- [x] GET /reports/cost-analysis 返回成本趋势和预测
- [x] GET /reports/cost-analysis 支持成本类型过滤 (compute/storage/network)
- [x] 报表生成时间 <5 秒

#### 报表导出
- [x] CSV 导出格式正确，包含所有必要字段
- [ ] PDF 导出使用 reportlab 生成格式化报表 (仅实现 CSV)
- [x] 支持自定义报表模板

#### 前端页面
- [x] 资源使用报表页面正确展示图表和表格
- [x] 资源使用报表支持导出 CSV
- [x] 成本分析仪表盘展示成本趋势折线图
- [x] 成本分析仪表盘展示成本分布饼图
- [x] 成本分析支持钻取到用户/项目级别
- [x] 成本趋势图表 (CostTrendChart) 支持对比上一周期

### Regression Evals
- [x] 成本计算不影响训练任务正常运行
- [x] Cost Explorer API 调用失败时返回缓存数据或明确错误
- [x] 认证和权限检查: 仅 admin 和 project_manager 可查看成本分析
- [x] 报表导出不泄露其他用户/项目的敏感数据

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- FR-018: 报表生成时间 <5 秒
- FR-019: 成本计算准确率 >98%
