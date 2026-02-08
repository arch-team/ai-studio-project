> **职责**: 项目特定配置 - 功能模块、路由、API 端点、环境变量（业务配置单一真实源）

# 项目配置 - AI Training Platform Frontend

> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-training-platform-frontend |
| **项目描述** | AI Training Platform - 基于 AWS Cloudscape 的企业级 AI 训练平台前端 |
| **架构模式** | Feature-Sliced Design (FSD) + Clean Architecture |
| **Node 版本** | >=18.0.0 |
| **源码根路径** | `src` |

---

## 技术栈版本要求

> **技术栈版本**: 详见 [rules/tech-stack.md](rules/tech-stack.md) (单一真实源)
>
> 如需项目特定的版本约束，请在 `package.json` 的 `engines` 或 `peerDependencies` 中定义。

---

## 功能模块

> **维护提示**: 新增功能时同步更新此表和 `src/features/` 目录。

| 功能 (Feature) | 职责 | 后端对应 |
|----------------|------|---------|
| `training` | 训练任务管理 | `modules/training` |
| `datasets` | 数据集管理 | `modules/datasets` |
| `models` | 模型管理 | `modules/models` |
| `spaces` | 开发空间管理 | `modules/spaces` |
| `audit` | 审计日志（只读） | `modules/audit` |
| `billing` | 成本统计 | `modules/billing` |
| `monitoring` | 集群监控 | `modules/monitoring` |
| `templates` | 训练模板 | `modules/templates` |
| `reports` | 报告分析 | `modules/reports` |
| `admin` | 管理功能 | `modules/admin` |
| `auth` | 用户认证与授权 (仅 Store) | `modules/auth` |
| `resource-quotas` | 资源配额管理 | `modules/quotas` |

---

## 路由配置

> **设计原则**: 路由结构反映业务领域，路由常量定义在 `src/app/router/routes.ts`。

| 路径 | 页面 | 功能模块 | 权限 |
|------|------|---------|------|
| `/` | 首页 | — | 需登录 |
| `/login` | 登录页 | `auth` | 公开 |
| `/training-jobs` | 训练任务列表 | `training` | 需登录 |
| `/training-jobs/:id` | 训练任务详情 | `training` | 需登录 |
| `/training-jobs/create` | 创建训练任务 | `training` | 需登录 |
| `/job-templates` | 任务模板列表 | `templates` | 需登录 |
| `/job-templates/:id` | 任务模板详情 | `templates` | 需登录 |
| `/job-templates/create` | 创建任务模板 | `templates` | 需登录 |
| `/models` | 模型列表 | `models` | 需登录 |
| `/models/:id` | 模型详情 | `models` | 需登录 |
| `/datasets` | 数据集列表 | `datasets` | 需登录 |
| `/datasets/:id` | 数据集详情 | `datasets` | 需登录 |
| `/checkpoints` | 检查点列表 | `datasets` | 需登录 |
| `/resource-quotas` | 资源配额 | `resource-quotas` | 需登录 |
| `/reports` | 报告 | `reports` | 需登录 |
| `/admin` | 管理后台 | `admin` | 管理员 |
| `/ide` | 开发空间 IDE | `spaces` | 需登录 |

---

## API 端点配置

> **位置约定**: 各模块 API 调用放在 `features/{module}/api/`，基础客户端在 `shared/api/client.ts`。

| 端点 | 用途 | 对应后端模块 |
|------|------|-------------|
| `/api/v1/auth/*` | 认证相关 | `auth` |
| `/api/v1/training-jobs/*` | 训练任务管理 | `training` |
| `/api/v1/datasets/*` | 数据集管理 | `datasets` |
| `/api/v1/models/*` | 模型管理 | `models` |
| `/api/v1/spaces/*` | 开发空间 | `spaces` |
| `/api/v1/resource-quotas/*` | 资源配额 | `quotas` |
| `/api/v1/job-templates/*` | 训练模板 | `templates` |
| `/api/v1/reports/*` | 报告分析 | `reports` |
| `/api/v1/admin/*` | 管理功能 | `admin` |
| `/api/v1/audit-logs/*` | 审计日志 | `audit` |
| `/api/v1/billing/*` | 成本统计 | `billing` |
| `/api/v1/monitoring/*` | 集群监控 | `monitoring` |

### API 客户端配置

> API 客户端实现（基于原生 fetch 的 `ApiClient`）详见 [rules/architecture.md](rules/architecture.md) §7.2

---

## 环境变量配置

> **位置**: `.env.example` 模板，`.env.local` 本地配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 基础 URL | `http://localhost:8000` |

---

## 导入路径配置

> 路径别名和导入规范详见 [rules/architecture.md](rules/architecture.md) §3 和 [rules/code-style.md](rules/code-style.md) §3

---

## 架构合规规则

> **详细规则**: 见 [rules/architecture.md](rules/architecture.md) §0.1 依赖合法性速查矩阵
