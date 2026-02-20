## EVAL: auth-system
Created: 2026-02-20
Module: backend/src/modules/auth/ + backend/src/shared/api/middleware/
Phase: 2 (Foundational)
Tasks: T011, T013-T013d

### Capability Evals

#### SSO 集成 (T013a)
- [ ] AWS IAM Identity Center (SAML 2.0/OIDC) 集成正确配置
- [ ] IdP 元数据正确解析和配置
- [ ] 用户自动映射: IdP 用户首次登录自动创建平台用户
- [ ] 角色同步: IdP 角色映射到平台角色 (admin/project_manager/engineer/viewer)
- [ ] SSO Token 验证正确提取用户信息

#### RBAC 策略 (T013b)
- [ ] 角色层次正确定义 (admin > project_manager > engineer > viewer)
- [ ] admin 角色拥有所有权限
- [ ] project_manager 可管理项目级资源配额和用户
- [ ] engineer 可创建/管理自己的训练任务和数据集
- [ ] viewer 仅有只读权限
- [ ] 基于资源的权限检查: 用户只能操作自己拥有的资源
- [ ] Kubernetes RBAC 集成: 平台角色映射到 K8s ClusterRole

#### 本地账号管理 (T013c)
- [ ] POST /auth/local-accounts 创建本地账号
- [ ] 密码强度验证: 最小 12 字符、大小写+数字+特殊字符
- [ ] 密码使用 bcrypt (cost factor >= 12) 或 argon2id 哈希
- [ ] 密码重置: 15 分钟有效期临时令牌
- [ ] 密码重置令牌使用后立即失效
- [ ] 账号锁定: 连续 5 次登录失败后锁定 30 分钟
- [ ] 密码历史: 禁止重复使用最近 5 个密码
- [ ] 错误响应使用通用消息 (不泄露账号存在性)

#### SSO 故障转移 (T013d)
- [ ] IdP 超时 (>5s) 时自动降级到本地账号认证
- [ ] 降级期间审计日志记录 auth_failover 操作
- [ ] SSO 恢复后 (健康检查通过) 自动切换回 SSO
- [ ] 本地账号不存在时返回适当错误 (不泄露信息)

#### 认证中间件 (T013)
- [ ] 验证 IAM Identity Center token 有效性
- [ ] Token 过期时返回 401
- [ ] Token 格式无效时返回 401
- [ ] 正确提取 user_id, role, email 等信息

### Regression Evals
- [ ] User 模型正确关联 resource_quotas
- [ ] 数据库迁移 (users 表) 可重复执行
- [ ] 认证中间件不影响 /docs 和 /health 端点访问
- [ ] SSO 和本地认证共享同一用户表
- [ ] 审计日志正确记录所有认证操作

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- SSO 故障转移时间 <10 秒
- 认证延迟 <50ms
- 密码安全标准符合 OWASP 最佳实践
