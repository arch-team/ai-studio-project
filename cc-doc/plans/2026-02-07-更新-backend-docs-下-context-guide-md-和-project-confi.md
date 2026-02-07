# 更新 backend/docs/ 下 context-guide.md 和 project-config.template.md

## Context

`backend/docs/` 下的两个文档（`context-guide.md` 和 `project-config.template.md`）是 backend 项目 `.claude/` 目录的导航说明和项目配置模板。随着项目开发推进，这两个文档与实际项目结构存在多处不一致，需要更新以保持同步。

---

## 差异分析

### context-guide.md 差异

| # | 差异项 | 文档现状 | 实际情况 |
|---|--------|---------|---------|
| 1 | `rules/` 文件数量 | 目录树显示 11 个文件 (正确)，但正文未提到实际数量匹配 | 实际 11 个文件，匹配 |
| 2 | skills 目录 | 未提及 | 根项目 `.claude/skills/` 存在两个 skill (decorator-exception, hyperpod-scheduling)，且 CLAUDE.md 和 project-config.md 均引用了 |
| 3 | 目录名称 | 多处写 `doc/` | 实际目录名是 `docs/` |
| 4 | `settings.local.json` | 描述了该文件 | 实际存在，描述正确 |
| 5 | 引用关系图 | 缺少 skills 相关引用 | project-config.md 引用了 skills |
| 6 | project-config 描述 | 说 template 位于 `doc/` 目录 | 实际位于 `docs/` 目录 |
| 7 | 架构合规测试位置 | 未特别说明 | 实际在 `tests/architecture/`（非 `tests/unit/`）|

### project-config.template.md 差异

| # | 差异项 | 模板现状 | 实际 project-config.md |
|---|--------|---------|----------------------|
| 1 | 架构合规测试路径 | `tests/unit/test_architecture_compliance.py` | 实际是 `tests/architecture/` 目录 |
| 2 | 模块表 | 只有 auth + 2 个占位符 | 实际有 9 个模块 |
| 3 | 域事件表 | 只有通用占位符 + auth | 实际有 6 个事件 |
| 4 | 技术栈补充 | 通用占位符 | 可参考实际 project-config.md 优化占位符 |
| 5 | 外部服务配置 | 通用 `infrastructure/external/` | 实际按模块分散放置 |
| 6 | 导入路径 | 缺少 Problem 异常相关导入 | 实际 project-config.md 包含完整导入路径 |
| 7 | 缺少章节 | 无"待解决问题"和"HyperPod 集成"章节模板 | 实际 project-config.md 包含这些实用章节 |

---

## 修改计划

### 文件 1: `backend/docs/context-guide.md`

**修改内容**：

1. **修正目录名称**: 所有 `doc/` 改为 `docs/`
2. **更新目录结构树**: 确认 rules 下 11 个文件列表正确
3. **补充 skills 引用说明**: 在文件说明部分新增 skills 目录的说明（位于根项目 `.claude/skills/`，非 backend 下）
4. **更新引用关系图**: 添加 project-config.md → skills 的引用箭头
5. **修正架构合规测试位置**: 将 `tests/unit/test_architecture_compliance.py` 更新为 `tests/architecture/`
6. **修正"相关资源"**: 更新项目仓库名称为 `ai-studio-project`

### 文件 2: `backend/docs/project-config.template.md`

**修改内容**：

1. **修正架构合规测试路径**: `tests/unit/test_architecture_compliance.py` → `tests/architecture/test_arch_*.py`
2. **优化模块表模板**: 参照实际结构增加"外部依赖"列
3. **优化域事件表模板**: 增加更具参考性的示例注释
4. **更新外部服务配置**: 说明适配器可按模块放置（不仅限于 `infrastructure/external/`）
5. **补充导入路径**: 添加 Problem 异常体系导入示例
6. **新增"待解决问题"模板章节**: 参照实际 project-config.md 格式
7. **新增"外部系统集成"模板章节**: 参照实际 HyperPod 集成章节
8. **更新架构合规测试表**: 匹配实际测试类名（`tests/architecture/`）

---

## 关键文件路径

| 文件 | 路径 |
|------|------|
| 待修改文件 1 | `backend/docs/context-guide.md` |
| 待修改文件 2 | `backend/docs/project-config.template.md` |
| 参照文件 - 实际配置 | `backend/.claude/project-config.md` |
| 参照文件 - CLAUDE.md | `backend/CLAUDE.md` |
| 参照文件 - 架构规范 | `backend/.claude/rules/architecture.md` |
| 参照文件 - 测试规范 | `backend/.claude/rules/testing.md` |

---

## 验证方式

1. 检查 `context-guide.md` 中所有引用的文件路径是否实际存在
2. 检查 `project-config.template.md` 中的测试路径、模板结构是否与实际 project-config.md 一致
3. 确认所有 `doc/` 已替换为 `docs/`
4. 确认引用关系图完整反映实际文件依赖
