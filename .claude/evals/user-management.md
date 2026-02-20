## EVAL: user-management
Created: 2026-02-20
Module: backend/src/modules/auth/ (users API) + frontend/src/features/admin/
Phase: 5 (US3)
Tasks: T055-T057, T064

### Capability Evals

#### 后端 API
- [ ] GET /users 支持分页
- [ ] GET /users 支持按 role 过滤 (admin/project_manager/engineer/viewer)
- [ ] GET /users 支持按 status 过滤 (active/disabled)
- [ ] GET /users 支持按 created_at 排序
- [ ] POST /users 创建用户并分配默认配额
- [ ] POST /users 创建 IAM Identity Center 用户
- [ ] POST /users 验证用户信息完整性 (username, email 唯一)
- [ ] PUT /users/{id} 更新用户角色
- [ ] PUT /users/{id} 更新用户状态 (active/disabled)
- [ ] PUT /users/{id} 更新配额关联
- [ ] 仅 admin 角色可管理用户

#### 前端页面
- [ ] 用户管理页面 (UserManagementPage) 正确渲染 Cloudscape Table
- [ ] 支持用户创建表单 (UserFormModal)
- [ ] 支持用户编辑和禁用操作
- [ ] 显示配额使用情况

### Regression Evals
- [ ] 用户删除/禁用不影响该用户已创建的训练任务和数据集
- [ ] 审计日志记录所有用户管理操作
- [ ] RBAC 权限正确应用
- [ ] 用户管理页面测试全部通过

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
