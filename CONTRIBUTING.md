# 贡献指南

感谢您对 AI 训练平台项目的关注！本文档将帮助您了解如何参与项目开发。

## 开发环境设置

### 前提条件

- Python 3.11+
- Node.js 18+ LTS
- Docker & Docker Compose
- AWS CLI v2 (已配置凭证)
- kubectl
- Git

### 本地环境搭建

1. **克隆仓库**

```bash
git clone <repository-url>
cd ai-studio-project
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，填入您的配置
```

3. **启动开发服务**

```bash
# 使用 Docker Compose 启动数据库
docker-compose up -d mysql

# 安装后端依赖
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn src.main:app --reload

# 新终端：安装前端依赖
cd frontend
npm install

# 启动前端开发服务器
npm run dev
```

## 代码规范

### Python (后端)

- **格式化**: 使用 `black` (行长度 88)
- **Lint**: 使用 `ruff`
- **类型检查**: 使用 `mypy`
- **导入排序**: 使用 `isort`

```bash
cd backend

# 格式化代码
black src/

# 检查代码风格
ruff check src/

# 类型检查
mypy src/

# 排序导入
isort src/
```

### TypeScript (前端)

- **格式化**: 使用项目配置的 ESLint
- **Lint**: 使用 ESLint + TypeScript 规则
- **类型检查**: TypeScript strict 模式

```bash
cd frontend

# 检查代码
npm run lint

# 类型检查
npm run build
```

### 命名规范

- **Python**:
  - 文件名: `snake_case.py`
  - 类名: `PascalCase`
  - 函数/变量: `snake_case`
  - 常量: `UPPER_SNAKE_CASE`

- **TypeScript**:
  - 文件名: `PascalCase.tsx` (组件), `camelCase.ts` (工具)
  - 组件: `PascalCase`
  - 函数/变量: `camelCase`
  - 类型/接口: `PascalCase`

## Git 工作流

### 分支命名

- `main`: 主分支，保持稳定
- `develop`: 开发分支
- `feature/<issue-id>-<short-description>`: 功能分支
- `fix/<issue-id>-<short-description>`: 修复分支
- `refactor/<short-description>`: 重构分支

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关
- `perf`: 性能优化

**示例**:

```bash
feat(training): add support for DeepSpeed ZeRO-3

Implements DeepSpeed ZeRO-3 configuration in training job creation.

Closes #123
```

### Pull Request 流程

1. 从 `develop` 创建功能分支
2. 完成开发并通过所有测试
3. 提交 PR 到 `develop`
4. 等待代码审查
5. 合并后删除功能分支

## 测试规范

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html

# 运行特定测试文件
pytest tests/test_training.py

# 运行特定测试函数
pytest tests/test_training.py::test_create_job
```

**覆盖率要求**:
- 核心功能 (P1): ≥80%
- 次要功能 (P2): ≥70%
- 辅助功能 (P3): ≥60%

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行带覆盖率的测试
npm run test:coverage

# 运行特定测试文件
npm test -- HomePage.test.tsx
```

## 项目结构

```
ai-studio-project/
├── backend/                    # 后端服务
│   ├── src/
│   │   ├── api/               # API 路由
│   │   │   └── v1/
│   │   │       └── endpoints/ # API 端点
│   │   ├── core/              # 核心配置
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务逻辑
│   │   ├── clients/           # 外部 API 客户端
│   │   └── middleware/        # 中间件
│   ├── alembic/               # 数据库迁移
│   └── tests/                 # 测试
├── frontend/                   # 前端应用
│   └── src/
│       ├── components/        # React 组件
│       ├── pages/             # 页面组件
│       ├── layouts/           # 布局组件
│       ├── store/             # Zustand 状态
│       ├── hooks/             # 自定义 Hooks
│       ├── lib/               # 工具函数
│       └── types/             # TypeScript 类型
├── infrastructure/             # IaC
│   └── cdk/                   # AWS CDK
├── specs/                      # 功能规范
└── docs/                       # 项目文档
```

## 设计原则

### HyperPod Native-First

优先使用 HyperPod 原生能力和 SDK：
1. `sagemaker-hyperpod` SDK (Training/Space/Cluster 模块)
2. HyperPod Add-ons (Training Operator, Kueue, Observability)
3. boto3 (非 HyperPod AWS 服务)
4. kubernetes-client (仅限 SDK 未覆盖的场景)

### UI 一致性

前端必须使用 AWS Cloudscape Design System，不允许使用其他 UI 框架。

### 代码质量

- SOLID 原则
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)

## 问题反馈

如果您发现 bug 或有功能建议，请创建 Issue 并包含：

1. **Bug 报告**:
   - 问题描述
   - 重现步骤
   - 期望行为
   - 实际行为
   - 环境信息

2. **功能请求**:
   - 功能描述
   - 使用场景
   - 期望的实现方式

## 联系方式

如有问题，请通过以下方式联系：

- 创建 GitHub Issue
- 发送邮件至 team@example.com
