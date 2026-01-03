# Quick Start Guide: 企业级AI训练平台

**Feature**: `001-ai-training-platform`
**Branch**: `001-ai-training-platform`
**Date**: 2026-01-03
**Phase**: Phase 1 - 开发环境搭建指南

---

## 概述

本文档提供企业级AI训练平台的快速开始指南,帮助开发人员在本地搭建完整的开发环境。

**预计完成时间**: 30-45 分钟

---

## 前置条件

### 系统要求

**操作系统**:
- macOS 12.0+ (推荐)
- Ubuntu 22.04 LTS
- Windows 11 + WSL2

**硬件要求**:
- CPU: 4 核以上
- RAM: 16 GB 以上
- 磁盘: 50 GB 可用空间

### 必需软件

1. **Python 3.11+**
```bash
python --version  # 应输出 Python 3.11.x
```

2. **Node.js 20+ 和 npm**
```bash
node --version    # 应输出 v20.x.x
npm --version     # 应输出 10.x.x
```

3. **Docker Desktop**
```bash
docker --version  # 应输出 Docker version 24.x.x
docker-compose --version  # 应输出 Docker Compose version v2.x.x
```

4. **Git**
```bash
git --version     # 应输出 git version 2.x.x
```

---

## Step 1: 克隆代码仓库

```bash
# 克隆项目
git clone <repository-url> ai-training-platform
cd ai-training-platform

# 切换到功能分支
git checkout 001-ai-training-platform
```

---

## Step 2: 后端环境搭建

### 2.1 安装 Python 依赖

**推荐使用 `uv` 包管理器** (research.md 推荐):

```bash
# 安装 uv (如未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
cd backend
uv venv --python 3.11

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -r requirements.txt
```

**requirements.txt 核心依赖**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
aiomysql==0.2.0
pydantic==2.5.3
pydantic-settings==2.1.0
boto3==1.34.20
sagemaker-hyperpod==0.1.0  # 注意: 实际版本可能不同
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### 2.2 启动 MySQL 数据库

**使用 Docker Compose**:

```bash
# 在项目根目录创建 docker-compose.yml
cd ..
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  mysql:
    image: mysql:8.0.28
    container_name: ai-training-mysql
    environment:
      MYSQL_ROOT_PASSWORD: dev_root_password
      MYSQL_DATABASE: ai_training_platform
      MYSQL_USER: dev_user
      MYSQL_PASSWORD: dev_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

volumes:
  mysql_data:
EOF

# 启动 MySQL
docker-compose up -d mysql

# 验证 MySQL 启动成功
docker ps | grep ai-training-mysql
```

**验证数据库连接**:
```bash
mysql -h 127.0.0.1 -u dev_user -pdev_password ai_training_platform -e "SELECT 'Connection successful!'"
```

### 2.3 配置环境变量

```bash
cd backend

# 创建 .env 文件
cat > .env <<EOF
# 数据库配置
DATABASE_URL=mysql+aiomysql://dev_user:dev_password@localhost:3306/ai_training_platform?charset=utf8mb4

# JWT 配置
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS 配置 (本地开发可使用占位符)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# HyperPod 配置 (本地开发可跳过)
HYPERPOD_CLUSTER_NAME=dev-cluster

# 应用配置
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
EOF
```

### 2.4 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 运行种子数据脚本 (创建管理员用户和默认配额)
python scripts/seed_data.py
```

**验证数据库初始化**:
```bash
mysql -h 127.0.0.1 -u dev_user -pdev_password ai_training_platform -e "SHOW TABLES;"
# 应该输出: users, resource_quotas, datasets, training_jobs, checkpoints, hyperpod_clusters
```

### 2.5 启动后端服务

```bash
# 启动 FastAPI 服务器 (开发模式,支持热重载)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 应输出:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [xxxxx] using StatReload
```

**验证后端 API**:
```bash
# 健康检查
curl http://localhost:8000/health
# 应输出: {"status":"healthy"}

# API 文档
open http://localhost:8000/docs  # macOS
# 或浏览器访问: http://localhost:8000/docs
```

---

## Step 3: 前端环境搭建

### 3.1 安装前端依赖

```bash
cd ../frontend

# 安装 npm 依赖
npm install

# 依赖安装完成后,验证
npm list --depth=0
# 应包含:
# @cloudscape-design/components@3.x.x
# react@18.x.x
# typescript@5.3.x
```

**package.json 核心依赖**:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@cloudscape-design/components": "^3.0.500",
    "@cloudscape-design/global-styles": "^1.0.10",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
```

### 3.2 配置前端环境变量

```bash
# 创建 .env.local 文件
cat > .env.local <<EOF
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_APP_ENV=development
EOF
```

### 3.3 启动前端开发服务器

```bash
# 启动 Vite 开发服务器 (支持热重载)
npm run dev

# 应输出:
# VITE v5.0.11  ready in xxx ms
# ➜  Local:   http://localhost:3000/
# ➜  Network: use --host to expose
```

**验证前端应用**:
```bash
open http://localhost:3000  # macOS
# 或浏览器访问: http://localhost:3000
```

---

## Step 4: 端到端测试

### 4.1 API 功能测试

**使用 curl 测试后端 API**:

```bash
# 1. 注册用户 (如未启用 IAM SSO,使用开发模式注册)
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "SecurePassword123!",
    "display_name": "Test User"
  }'

# 2. 登录获取 Token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'
# 应返回: {"access_token": "eyJhbGc...", "token_type": "bearer"}

# 3. 使用 Token 查询训练任务 (应返回空列表)
export TOKEN="<上一步返回的 access_token>"
curl -X GET http://localhost:8000/v1/training-jobs \
  -H "Authorization: Bearer $TOKEN"
# 应返回: {"items": [], "total": 0, "page": 1, "page_size": 20}
```

### 4.2 前端集成测试

1. **登录测试**:
   - 访问 http://localhost:3000
   - 使用测试用户登录 (testuser / SecurePassword123!)
   - 验证跳转到仪表板页面

2. **创建训练任务测试** (模拟创建,需要 HyperPod 集群):
   - 点击 "新建训练任务" 按钮
   - 填写任务基本信息:
     - 任务名称: `test-training-job`
     - 镜像 URI: `pytorch/pytorch:2.1.0-cuda11.8`
     - 实例类型: `ml.p4d.24xlarge`
     - 节点数量: `2`
   - 提交任务 (如无 HyperPod 集群,会返回错误,预期行为)

3. **数据集管理测试**:
   - 导航到 "数据集" 页面
   - 创建测试数据集
   - 验证数据集列表显示

---

## Step 5: 开发工作流

### 5.1 后端开发

**目录结构**:
```
backend/
├── src/
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/                   # 核心配置 (database.py, config.py)
│   ├── models/                 # SQLAlchemy ORM 模型
│   ├── schemas/                # Pydantic 数据模型
│   ├── repositories/           # 数据访问层
│   ├── services/               # 业务逻辑层
│   ├── api/v1/                 # API 路由
│   └── utils/                  # 工具函数
├── alembic/                    # 数据库迁移
├── tests/                      # 单元测试和集成测试
└── requirements.txt            # Python 依赖
```

**开发命令**:
```bash
# 运行单元测试
pytest tests/unit

# 运行集成测试
pytest tests/integration

# 代码格式化
black src/
ruff check src/ --fix

# 类型检查
mypy src/
```

### 5.2 前端开发

**目录结构**:
```
frontend/
├── src/
│   ├── main.tsx                # React 应用入口
│   ├── App.tsx                 # 根组件
│   ├── layouts/                # 布局组件 (MainLayout.tsx)
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard/
│   │   ├── Jobs/
│   │   ├── Datasets/
│   │   └── Settings/
│   ├── components/             # 共享组件
│   ├── stores/                 # Zustand 状态管理
│   ├── api/                    # TanStack Query Hooks
│   └── types/                  # TypeScript 类型定义
└── package.json
```

**开发命令**:
```bash
# 运行 TypeScript 类型检查
npm run type-check

# 代码格式化
npm run format

# Linting
npm run lint

# 构建生产版本
npm run build
```

---

## Step 6: 常见问题排查

### 6.1 数据库连接失败

**问题**: `sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**:
```bash
# 1. 检查 MySQL 容器状态
docker ps | grep ai-training-mysql

# 2. 检查端口占用
lsof -i :3306

# 3. 重启 MySQL 容器
docker-compose restart mysql

# 4. 验证数据库配置
echo $DATABASE_URL  # 检查 .env 文件中的连接字符串
```

### 6.2 前端 API 请求跨域错误

**问题**: `Access to XMLHttpRequest blocked by CORS policy`

**解决方案**: 后端已配置 CORS,检查 `src/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 开发环境允许
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.3 Python 依赖安装失败

**问题**: `error: externally-managed-environment`

**解决方案**: 使用虚拟环境
```bash
# 使用 uv (推荐)
uv venv --python 3.11
source .venv/bin/activate

# 或使用 venv
python -m venv .venv
source .venv/bin/activate
```

### 6.4 前端依赖安装失败

**问题**: `npm ERR! code ERESOLVE`

**解决方案**:
```bash
# 清理 npm 缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

---

## Step 7: 下一步

完成本地环境搭建后,建议阅读以下文档:

1. **[data-model.md](./data-model.md)**: 了解数据库表结构和实体关系
2. **[contracts/training-jobs-api.yaml](./contracts/training-jobs-api.yaml)**: 查看训练任务 API 详细文档
3. **[research.md](./research.md)**: 深入了解技术选型和架构设计

**开发任务建议**:
- 熟悉 FastAPI 项目结构和依赖注入
- 学习 AWS Cloudscape Design System 组件库
- 理解 SQLAlchemy 2.0 异步 ORM 模式
- 掌握 TanStack Query 数据缓存和同步机制

---

## 附录

### A. 常用开发命令

**后端**:
```bash
# 激活虚拟环境
source backend/.venv/bin/activate

# 启动后端服务
cd backend && uvicorn src.main:app --reload

# 运行测试
pytest tests/

# 创建数据库迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head
```

**前端**:
```bash
# 启动前端服务
cd frontend && npm run dev

# 类型检查
npm run type-check

# 构建生产版本
npm run build
```

**数据库**:
```bash
# 连接 MySQL
mysql -h 127.0.0.1 -u dev_user -pdev_password ai_training_platform

# 查看表
SHOW TABLES;

# 查看表结构
DESCRIBE training_jobs;
```

### B. 开发环境 URL 一览

| 服务 | URL | 说明 |
|------|-----|------|
| 前端应用 | http://localhost:3000 | React + Vite 开发服务器 |
| 后端 API | http://localhost:8000 | FastAPI 服务器 |
| API 文档 (Swagger UI) | http://localhost:8000/docs | 交互式 API 文档 |
| API 文档 (ReDoc) | http://localhost:8000/redoc | 可读性更好的 API 文档 |
| MySQL 数据库 | localhost:3306 | MySQL 8.0.28 |

### C. 推荐 IDE 配置

**VS Code 推荐扩展**:
- Python: `ms-python.python`
- Pylance: `ms-python.vscode-pylance`
- TypeScript: 内置
- ESLint: `dbaeumer.vscode-eslint`
- Prettier: `esbenp.prettier-vscode`

**VS Code 设置** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-03
**审核状态**: Phase 1 设计完成
