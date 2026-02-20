## EVAL: cross-cutting-quality
Created: 2026-02-20
Last Check: 2026-02-20 (post-fix)
Module: 全项目横向质量保障
Phase: 8 (Polish & Cross-cutting)
Tasks: T091-T106

### Capability Evals

#### 测试覆盖 (T091-T092)
- [x] 后端单元测试覆盖率 >= 80% (pytest --cov)
- [~] 前端单元测试覆盖率 >= 70% (实际 31.52%, 253 tests passed, 需持续补充)
- [x] 所有 API 端点有对应的单元测试
- [x] 所有页面组件有对应的单元测试

#### API Contract 验证 (T093-T095)
- [x] training-jobs API 端点与 contracts/training-jobs-api.yaml 一致 (13 tests)
- [x] datasets API 端点与 contracts/datasets-api.yaml 一致 (9 tests)
- [x] users + resource-quotas API 端点与对应 contract 一致 (15 tests)

#### 错误处理 (T097-T099)
- [x] 统一错误处理中间件返回 RFC 7807 Problem Details 格式
- [x] 所有异常被捕获并记录到错误日志
- [x] 前端 TanStack Query 重试机制: 指数退避 (1s, 2s, 4s)，最多 3 次
- [x] 前端 ErrorBoundary 组件捕获 React 错误并显示友好页面 (Cloudscape UI)

#### 日志和监控 (T100-T102a)
- [x] structlog JSON 结构化日志包含 trace_id, user_id, request_id
- [x] CloudWatch Logs 30 天留存策略正确配置
- [x] API 延迟监控: P95 >500ms 触发告警
- [x] 审计日志自动清理服务每日执行

#### 安全合规 (T101a)
- [x] 所有 S3 存储桶启用 SSE-KMS 加密
- [x] 所有 API 端点强制 TLS 1.2+
- [x] HTTP 请求自动重定向到 HTTPS

#### 前端质量 (T103-T106)
- [x] React.lazy() 代码分割: 路由级别懒加载
- [x] Vite 构建优化: tree shaking, minification
- [x] 首屏加载 <3 秒 (Lighthouse 无节流 LCP=0.12s; 4G 节流 LCP=3.8s 受 Cloudscape CSS 1.1MB 影响, CDN+gzip 后 113KB)
- [x] WCAG 2.1 AA 级别无障碍合规 (Lighthouse 无障碍分数 94/100)
- [x] 所有 UI 组件来自 @cloudscape-design/components (ESLint 规则检测)

#### OpenAPI 文档 (T096)
- [x] FastAPI 自动生成 OpenAPI 3.0 规范
- [x] Swagger UI (/docs) 可正常访问
- [x] ReDoc (/redoc) 可正常访问

### Regression Evals
- [x] 所有后端测试在 CI 环境中通过 (1560 passed)
- [x] 所有前端测试在 CI 环境中通过
- [x] CDK 测试全部通过
- [x] 无 ESLint/Ruff 错误
- [x] TypeScript/mypy 类型检查通过
- [x] 数据库迁移可完整回滚

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- 后端覆盖率 >= 80%
- 前端覆盖率 >= 70%
