# Serena Memory 策略详解

## Memory 概述

Serena MCP 提供持久化记忆功能，支持跨会话的知识存储与检索。

**核心操作**:
- `write_memory(key, content)` - 写入记忆
- `read_memory(key)` - 读取记忆
- `list_memories()` - 列出所有记忆
- `delete_memory(key)` - 删除记忆
- `edit_memory(key, content)` - 编辑记忆

## Memory vs CLAUDE.md vs Rules

| 特性 | Memory | CLAUDE.md | Rules |
|------|--------|-----------|-------|
| 加载时机 | 按需读取 | 会话开始 | 文件匹配时 |
| Token 影响 | 仅读取时 | 每次对话 | 触发时 |
| 持久性 | 跨会话 | 文件级 | 配置级 |
| 容量 | 无限制 | 建议<200行 | 建议<500 token/rule |
| 适用场景 | 动态知识 | 静态规范 | 文件规则 |

## 使用场景

### 1. 架构决策记录 (ADR)

```
write_memory("adr_001_database", """
# ADR-001: 数据库选型

## 状态
已采纳 (2024-01-15)

## 背景
需要支持高并发训练任务元数据存储

## 决策
选择 DynamoDB 而非 PostgreSQL

## 理由
- 无限扩展能力
- AWS 原生集成
- 按需付费模式

## 后果
- 需要设计好分区键
- 复杂查询需要 GSI
""")
```

### 2. 技术研究报告

```
write_memory("research_auth_options", """
# 认证方案研究

## 选项比较

| 方案 | 优点 | 缺点 |
|------|------|------|
| Cognito | AWS 原生 | 定制困难 |
| Auth0 | 功能丰富 | 成本高 |
| 自建 JWT | 灵活 | 维护成本 |

## 推荐
Cognito + 自定义 Lambda 触发器

## 参考
- https://docs.aws.amazon.com/cognito/
""")
```

### 3. 会话状态持久化

```
write_memory("session_feature_auth", """
# 认证功能实现进度

## 已完成
- [x] 用户模型设计
- [x] Cognito 集成
- [x] JWT 验证中间件

## 进行中
- [ ] 角色权限系统

## 待办
- [ ] OAuth2 社交登录
- [ ] 双因素认证

## 当前阻塞
等待安全团队审核 Cognito 配置
""")
```

### 4. 检查点备份

```
write_memory("checkpoint_20240118_1430", """
# 工作检查点

## 当前分支
feature/auth-system

## 未提交更改
- src/auth/middleware.py (新增)
- src/api/routes/auth.py (修改)

## 下一步
实现 refresh token 逻辑

## 上下文
参考 research_auth_options 的决策
""")
```

## Memory Key 命名规范

### 命名模式

| 类别 | 模式 | 示例 |
|------|------|------|
| 架构决策 | `adr_{number}_{topic}` | `adr_001_database` |
| 技术研究 | `research_{topic}` | `research_auth_options` |
| 会话状态 | `session_{feature}` | `session_auth_impl` |
| 检查点 | `checkpoint_{date}_{time}` | `checkpoint_20240118_1430` |
| 项目配置 | `config_{name}` | `config_aws_regions` |
| 问题记录 | `issue_{id}` | `issue_perf_bottleneck` |

### 命名原则

1. **小写下划线**: `snake_case`
2. **语义清晰**: 从名称推断内容
3. **分类前缀**: 便于 `list_memories()` 筛选
4. **避免过长**: <50 字符

## 工作流模式

### 会话开始

```python
# 1. 检查现有记忆
list_memories()

# 2. 读取相关上下文
read_memory("session_current_feature")
read_memory("adr_latest")

# 3. 思考收集的信息
think_about_collected_information()
```

### 工作过程中

```python
# 定期保存进度
write_memory("checkpoint_latest", current_state)

# 记录重要决策
write_memory("decision_api_design", rationale)

# 验证任务方向
think_about_task_adherence()
```

### 会话结束

```python
# 1. 检查完成状态
think_about_whether_you_are_done()

# 2. 保存会话总结
write_memory("session_summary_20240118", outcomes)

# 3. 清理临时记忆
delete_memory("checkpoint_temp")
```

## 内容组织

### 推荐格式

```markdown
# [标题]

## 状态/概述
[当前状态或简要概述]

## 主体内容
[详细信息，使用列表/表格]

## 相关
- 链接到其他 memory key
- 相关文档引用

## 更新日志
- 2024-01-18: 初始创建
```

### 内容长度指南

| 类型 | 建议长度 | 说明 |
|------|---------|------|
| 决策记录 | 200-500 字 | 重点是"为什么" |
| 技术研究 | 500-1000 字 | 包含对比和结论 |
| 会话状态 | 100-300 字 | 简洁的进度跟踪 |
| 检查点 | 50-200 字 | 仅核心上下文 |

## 与其他机制配合

### Memory → CLAUDE.md

当 Memory 中的决策变为长期规范：

```
# 在 Memory 中验证决策
write_memory("adr_db_choice", "选择 DynamoDB...")

# 决策稳定后，添加到 CLAUDE.md
# CLAUDE.md:
## 技术约束
- 数据库: DynamoDB (见 ADR-001)
```

### Memory → Rules

当 Memory 中的模式需要自动应用：

```
# Memory 中记录模式
write_memory("pattern_api_error", "所有 API 使用统一错误格式...")

# 成为规范后，创建 Rules 文件
# .claude/rules/api.md:
```

```markdown
---
paths:
  - "src/api/**"
---

# API Rules

- 使用统一错误响应格式 ErrorResponse
```

## 清理策略

### 定期清理

```python
# 列出所有记忆
memories = list_memories()

# 识别过期记忆
# - checkpoint_* 超过 7 天
# - session_* 已完成的功能

# 删除过期记忆
delete_memory("checkpoint_20240101")
```

### 归档策略

重要但不常用的记忆，考虑：
1. 导出到项目 `docs/decisions/` 目录
2. 更新 memory 为引用：`"详见 docs/decisions/adr-001.md"`

## 最佳实践

### DO

- 为重要决策创建 ADR 记忆
- 会话开始时检查相关记忆
- 定期保存工作检查点
- 使用清晰的命名规范
- 清理已完成的临时记忆

### DON'T

- 不要存储大量代码片段 (用 Git)
- 不要复制 CLAUDE.md 内容
- 不要创建过多细粒度记忆
- 不要忽略记忆的更新维护
