## EVAL: us1-templates
Created: 2026-02-20
Module: backend/src/modules/training/ (templates) + frontend/src/features/templates/
Phase: 3 (P1 Must-Have)
Tasks: T200-T203

### Capability Evals

#### 后端 API
- [ ] POST /job-templates 能创建训练任务模板
- [ ] GET /job-templates 支持按可见性 (private/team/public) 过滤
- [ ] GET /job-templates 支持按热度 (usage_count) 排序
- [ ] GET /job-templates/popular 返回热门模板列表
- [ ] GET /job-templates/{id} 返回模板详情含完整 training_config
- [ ] PUT /job-templates/{id} 仅模板所有者可更新
- [ ] DELETE /job-templates/{id} 执行软删除
- [ ] POST /training-jobs/from-template/{template_id} 基于模板创建训练任务并递增 usage_count

#### 领域模型
- [ ] JobTemplate 实体正确实现可见性控制 (private/team/public)
- [ ] JobTemplate 实体 training_config JSON 存储和反序列化正确
- [ ] 基于模板创建任务时正确合并用户自定义配置

#### 前端页面
- [ ] 模板列表页面 (TemplateListPage) 正确渲染 Cloudscape Table
- [ ] 模板详情页面 (TemplateDetailPage) 展示 training_config 和使用统计
- [ ] 热门模板组件 (PopularTemplates) 正确渲染卡片布局

### Regression Evals
- [ ] 模板 CRUD 操作正确记录审计日志
- [ ] 模板删除不影响已基于该模板创建的训练任务
- [ ] 认证和权限检查正确应用

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
