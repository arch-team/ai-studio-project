# AI Training Platform - 企业级AI训练平台

基于AWS SageMaker HyperPod构建的企业级AI训练平台，支持分布式训练、资源调度、数据管理和多租户。

## 功能特性

- ✅ **分布式训练管理**: 支持PyTorch DDP、FSDP、DeepSpeed等框架
- ✅ **资源调度**: Gang Scheduling和基于优先级的抢占式调度
- ✅ **数据集管理**: 大文件断点续传、版本控制和高性能存储
- ✅ **实时监控**: 训练进度、资源使用和成本分析
- ✅ **弹性恢复**: 自动恢复和分层检查点存储
- ✅ **多租户支持**: 资源配额和细粒度权限控制

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (异步ORM)
- Alembic (数据库迁移)
- PostgreSQL
- Redis
- AWS SDK (Boto3)
- Kubernetes Python Client

### 前端
- TypeScript
- React 18
- React Router v6
- Zustand (状态管理)
- TanStack Query
- Vite
- Recharts (图表)

### 基础设施
- AWS SageMaker HyperPod with EKS
- HyperPod Training Operator
- HyperPod Task Governance (Kueue)
- HyperPod Observability Add-on
- Amazon FSx for Lustre
- Amazon S3
- Amazon EFS

## 快速开始

### 前提条件

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- AWS CLI (已配置)
- kubectl

### 本地开发

1. **克隆仓库**
```bash
git clone <repository-url>
cd ai-training-platform
```

2. **配置环境变量**
```bash
# 后端
cp backend/.env.example backend/.env
# 根据需要修改 backend/.env

# 前端
cp frontend/.env.example frontend/.env
# 根据需要修改 frontend/.env
```

3. **启动开发环境**
```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 或者分别启动后端和前端

# 后端
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

4. **访问应用**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 数据库迁移

```bash
cd backend

# 创建迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 项目结构

```
.
├── backend/                 # 后端服务
│   ├── src/                # 源代码
│   │   ├── api/           # API层
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── config/        # 配置
│   ├── k8s/               # Kubernetes资源
│   ├── alembic/           # 数据库迁移
│   ├── tests/             # 测试
│   └── requirements.txt   # Python依赖
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API客户端
│   │   └── types/         # TypeScript类型
│   └── package.json       # Node依赖
├── infra/                  # 基础设施代码
│   ├── cdk/               # AWS CDK
│   ├── helm/              # Helm charts
│   └── argocd/            # ArgoCD配置
├── specs/                  # 功能规范
└── docker-compose.yml      # 本地开发配置
```

## 开发指南

### 代码风格

**Python:**
- 使用 `black` 进行代码格式化
- 使用 `ruff` 进行代码检查
- 使用 `mypy` 进行类型检查

```bash
cd backend
black src/
ruff check src/
mypy src/
```

**TypeScript:**
- 使用 `prettier` 进行代码格式化
- 使用 `eslint` 进行代码检查

```bash
cd frontend
npm run format
npm run lint
```

### 测试

**后端测试:**
```bash
cd backend
pytest
pytest --cov=src --cov-report=html
```

**前端测试:**
```bash
cd frontend
npm test
npm run test:coverage
```

## 部署

### Kubernetes部署

1. **配置Kubeconfig**
```bash
aws eks update-kubeconfig --name <cluster-name> --region <region>
```

2. **使用Helm部署**
```bash
cd infra/helm
helm install ai-platform ./ai-platform -n ai-training-platform --create-namespace
```

3. **使用ArgoCD部署（GitOps）**
```bash
kubectl apply -f infra/argocd/applications/
```

## 监控和日志

- **Prometheus**: http://<cluster-url>:9090
- **Grafana**: http://<grafana-url>
- **HyperPod Observability**: 集成在AWS Console

## 文档

- [功能规范](./specs/001-ai-training-platform/spec.md)
- [实施计划](./specs/001-ai-training-platform/plan.md)
- [数据模型](./specs/001-ai-training-platform/data-model.md)
- [API文档](http://localhost:8000/docs)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- 项目维护者: [Your Team]
- 邮箱: team@example.com
