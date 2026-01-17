# 清理遗留空目录计划

> **问题**: `git rm -rf` 删除了文件，但 `__pycache__` 缓存文件（在 `.gitignore` 中）未被删除，导致空目录壳仍然存在。

## 需要删除的目录

### integration/ 下的遗留目录
```
integration/api/          # 只剩 __pycache__
integration/aws/          # 只剩 __pycache__
integration/middleware/   # 只剩 __pycache__
integration/modules/      # 只剩 __pycache__（包含多层子目录）
```

### unit/ 下的遗留目录（如果存在）
需要检查是否也有类似问题。

## 执行命令

```bash
# 删除 integration 遗留目录
rm -rf integration/api integration/aws integration/middleware integration/modules

# 删除 unit 遗留目录（如有）
rm -rf unit/api unit/core unit/domain unit/application unit/infrastructure unit/modules

# 验证
ls integration/
ls unit/
```

## 验证

清理后目录应该只包含：

```
integration/
├── auth/
├── models/
├── quotas/
├── shared/
└── training/

unit/
├── audit/
├── auth/
├── models/
├── quotas/
├── shared/
└── training/
```
