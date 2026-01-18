# Token 效率优化原则

## Token 预算概念

Claude Code 每次对话都有上下文限制。合理分配 token 预算确保：
- 关键信息始终可用
- 避免上下文截断
- 保持响应质量

## Token 分配策略

### 总体预算分配

| 类别 | Token 占比 | 绝对值参考 |
|------|-----------|-----------|
| CLAUDE.md (全局+项目) | 5-10% | 2000-5000 |
| Rules (触发时) | 1-3% | 500-1500 |
| Memory (读取时) | 按需 | 无固定上限 |
| 对话历史 | 40-60% | - |
| 工作空间 | 30-40% | - |

### CLAUDE.md Token 分配

```
~/.claude/CLAUDE.md:     500-1000 tokens
project/CLAUDE.md:       1000-2000 tokens
子目录 CLAUDE.md (累加):  300-500 tokens/每个
───────────────────────────────────
总计:                    ~3000-5000 tokens
```

## 优化技术

### 1. 符号压缩

使用符号替代冗长描述：

```markdown
# 低效 ❌
## 开发流程
开发时必须先编写测试，然后编写使测试通过的最少代码，最后重构代码同时保持测试通过。

# 高效 ✓
## 开发流程
TDD: 🔴Red → 🟢Green → 🔄Refactor
```

### 2. 表格替代列表

```markdown
# 低效 ❌
## 术语
- 训练任务的英文是 Training Job
- 训练任务对应的 Python 类是 TrainingJob
- 训练任务在数据库中的表名是 training_jobs
- 训练任务的 API 路径是 /training-jobs

# 高效 ✓
## 术语
| 中文 | 英文 | 类 | 表 | API |
|------|------|-----|-----|------|
| 训练任务 | Training Job | TrainingJob | training_jobs | /training-jobs |
```

### 3. 引用替代复制

```markdown
# 低效 ❌
## 架构
[复制 100 行架构说明]

# 高效 ✓
## 架构
> 详见 `docs/ARCHITECTURE.md`
> DDD + Clean Architecture，依赖方向: API → App → Domain ← Infra
```

### 4. 缩写系统

定义项目缩写，在 CLAUDE.md 中使用：

```markdown
## 缩写
- TJ: TrainingJob (训练任务)
- DS: Dataset (数据集)
- CP: Checkpoint (检查点)
- RQ: ResourceQuota (资源配额)

## 状态机
TJ: submitted → running → completed|failed|paused
```

### 5. 层级委托

```markdown
# 根 CLAUDE.md (简洁)
## 后端
> 详见 `backend/CLAUDE.md`

# backend/CLAUDE.md (详细)
[后端特定的详细配置]
```

## 内容分类决策

### 放入 CLAUDE.md

✅ 每次对话都需要的信息：
- 响应语言设置
- 核心架构约束
- 术语标准表
- 关键文档索引

### 移到 Rules

✅ 条件性触发的规范：
- 文件类型特定规则
- 测试规范
- 配置文件规则

### 移到 Memory

✅ 偶尔参考的内容：
- 历史决策记录
- 技术研究报告
- 会话状态

### 移到外部文档

✅ 详细但非必需的内容：
- 完整 API 文档
- 详细架构说明
- 操作手册

## 检测与优化

### Token 估算公式

```
英文: ~4 字符 = 1 token
中文: ~2 字符 = 1 token
代码: ~3-4 字符 = 1 token
```

### 快速估算

```
CLAUDE.md 行数 × 20 ≈ token 数
(假设平均每行 60-80 字符)
```

### 优化检查清单

1. **重复检测**
   - [ ] 子目录是否重复父级内容？
   - [ ] 多个文件是否有相同段落？

2. **分类检查**
   - [ ] 高频内容是否在 CLAUDE.md？
   - [ ] 条件内容是否用 Rules？
   - [ ] 低频内容是否用 Memory？

3. **压缩检查**
   - [ ] 是否可以用表格替代列表？
   - [ ] 是否可以用符号替代文字？
   - [ ] 是否可以引用替代复制？

## 层级内容分布

### 根 CLAUDE.md (~100行)

```markdown
# CLAUDE.md

## 响应语言 (2行)
## 项目概述 (5行)
## 核心约束 (10行)
## 术语标准 (20行表格)
## 关键文档 (10行表格)
## 开发原则 (15行)
## 模块索引 (10行)
───────────────
合计: ~72行 + 标题 ≈ 100行
Token: ~2000
```

### 子目录 CLAUDE.md (~40行)

```markdown
# Backend CLAUDE.md

## 继承说明 (2行)
## 技术栈 (5行)
## 目录结构 (10行)
## 测试命令 (5行)
## 特殊规范 (10行)
───────────────
合计: ~32行 + 标题 ≈ 40行
Token: ~800
```

## 动态调整策略

### 上下文紧张时

当检测到上下文使用 >75%：

1. **减少 CLAUDE.md 加载**
   - 仅加载直接相关的子目录配置

2. **延迟 Memory 读取**
   - 仅在明确需要时读取

3. **简化输出**
   - 使用符号和缩写
   - 减少解释性文字

### 资源充足时

上下文使用 <50%：

1. **完整上下文**
   - 加载所有相关 CLAUDE.md

2. **主动读取 Memory**
   - 获取历史决策背景

3. **详细输出**
   - 提供完整解释

## 工具支持

### `/context-architect:optimize` 命令

自动分析并优化：
- 检测重复内容
- 估算 token 占用
- 提供精简建议
- 生成优化后版本

### 手动检查

```bash
# 统计 CLAUDE.md 行数
find . -name "CLAUDE.md" -exec wc -l {} \;

# 估算总 token
find . -name "CLAUDE.md" -exec cat {} \; | wc -c
# 字符数 / 3 ≈ token 数
```
