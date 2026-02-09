# 技术栈规范

> **职责**: 技术栈版本要求的**单一真实源**，包括 Python、AWS CDK、pytest 等核心依赖版本。

---

## §0 速查卡片

### 版本要求矩阵

| 类别 | 技术 | 最低版本 | 推荐版本 |
|------|------|---------|---------|
| **核心** | Python | >=3.11 | 3.12+ |
| **核心** | AWS CDK | >=2.150.0 | 2.170.0+ |
| **核心** | aws-cdk-lib | >=2.150.0 | 2.170.0+ |
| **核心** | constructs | >=10.0.0 | 10.4+ |
| **测试** | pytest | >=7.0.0 | 8.x |
| **测试** | pytest-cov | >=4.0.0 | 5.x |
| **安全** | cdk-nag | >=2.28.0 | 2.30+ |
| **代码质量** | ruff | >=0.4.0 | 0.8+ |
| **代码质量** | mypy | >=1.8.0 | 1.13+ |

### 关键约束

- **包管理器**: pip + requirements.txt (或 uv)
- **Python**: `mypy --strict` 必须启用
- **CDK CLI**: 全局安装 `npm install -g aws-cdk`

### 快速验证命令

```bash
# 检查核心版本
python --version && cdk --version

# 检查依赖版本
pip list | grep -E "aws-cdk-lib|constructs|pytest|ruff|mypy|cdk-nag"
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [code-style.md](code-style.md) | ruff/mypy 配置详情 |
| [testing.md](testing.md) | pytest 配置和测试规范 |
