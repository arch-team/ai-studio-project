---
paths:
  - "backend/src/**/*.py"
---

# Clean Architecture 规范

项目采用 DDD + Modular Monolith + Clean Architecture 架构模式。

## 依赖方向

```
API → Application → Domain ← Infrastructure
```

**黄金法则**: 内层不依赖外层，Domain 层是核心。

## 职责边界

| 层级 | 职责 | 禁止 |
|------|------|------|
| **Entity** | 业务规则、状态转换 | 数据库访问、外部调用 |
| **Service** | 用例编排、事务协调 | HTTP 处理、SQL 语句 |
| **Repository** | 数据持久化 | 业务逻辑、验证规则 |
| **Endpoint** | HTTP 转换、参数验证 | 业务逻辑、直接 DB 访问 |

## 模块边界检查

- 每个模块文件 < 300 行（超过则考虑拆分）
- 每个类 < 10 个公开方法
- 模块间通过接口通信，不直接依赖实现

## 模块间通信

- 使用事件驱动 + 共享接口
- 禁止跨模块直接导入实现类
- 通过 `shared/domain/` 定义跨模块接口
