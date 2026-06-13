# SQLAlchemy Enum 持久化大小写修复方案

> 关联 Issue: #3
> 日期: 2026-06-13
> 性质: 生产风险修复（auth 鉴权链路受影响，紧迫度最高）
> 范式来源: monitoring 模块已落地的修复（PR #2 / `hyperpod_cluster_model.py`）

---

## 1. 问题本质

SQLAlchemy `Enum(SomeEnum)` 默认按**成员名**（`.name`，如 `ACTIVE`）读写数据库。当 Python enum 的 `.value` 是小写（`"active"`）、且 alembic 迁移把 DB ENUM 列定义为**小写值**时，从真实 DB 读回的 `'active'` 无法匹配成员名集合 `{ACTIVE, ...}`，抛：

```
LookupError: 'active' is not among the defined enum values. Possible values: ACTIVE, INACTIVE, ...
```

**触发条件（三者同时满足才"真坏"）**：
1. enum 成员名 ≠ `.value`（名大写、值小写）
2. ORM 列未设 `values_callable`
3. 迁移把该列定义为小写值

monitoring 模块已用 `values_callable` 修复，是本方案的范式模板。

---

## 2. 影响范围（已调研确认）

### 2.1 确认受影响：3 模块 10 列

| 模块 | 表 | 列 | enum | DB 列大小写 |
|------|----|----|------|-----------|
| auth | `users` | `status` | `UserStatus` | 小写 |
| auth | `users` | `role` | `UserRole` | 小写 |
| auth | `users` | `auth_type` | `AuthType` | 小写 |
| quotas | `resource_quotas` | `quota_type` | `QuotaType` | 小写 |
| quotas | `resource_quotas` | `status` | `QuotaStatus` | 小写 |
| quotas | `resource_limit_configs` | `role` | `LimitRole` | 小写 |
| quotas | `resource_limit_configs` | `priority_default` | `PriorityDefault` | 小写 |
| audit | `audit_logs` | `operation_type` | `ModelOperationType`（ORM 本地枚举） | 小写 |
| audit | `audit_logs` | `resource_type` | `ModelResourceType`（ORM 本地枚举） | 小写 |
| audit | `audit_logs` | `status` | `ModelAuditStatus`（ORM 本地枚举） | 小写 |

### 2.2 明确不受影响（切勿改动）

| 模块 | 原因 |
|------|------|
| **spaces** | enum 名≠值，但 DB 列存**大写成员名**，SA 默认按 `.name` 读写，self-consistent。**给 spaces 加 `values_callable` 反而会弄坏它。** |
| monitoring | 已修复 |
| datasets / models / training | enum 名==值（全大写），不受影响 |

### 2.3 紧迫度

- 🔴 **auth.users 三列在鉴权主链路**（登录、`get_current_user`、用户管理）——只要 users 表有真实数据，几乎所有需登录的请求 500。**最优先。**
- 🔴 quotas 在配额检查/限额配置路径，真实读回即崩。
- 🟠 audit 在每个写操作的审计中间件，写入失败可能丢审计或抛错。

---

## 3. 修复方案

### 3.1 前置确认（修复前必做）

迁移历史经历三次大小写反复，**必须先核对目标环境 DB 真实状态**，确认已落到最终小写态（迁移 `h8i9j0k1l2m3` / `20260222_100400_fix_enum_values_to_lowercase`）：

```sql
SELECT version_num FROM alembic_version;  -- 确认 = j0k1l2m3n4o5（最新 head）
SHOW COLUMNS FROM users LIKE 'status';    -- 确认 enum('active','inactive',...) 小写
SHOW COLUMNS FROM resource_quotas LIKE 'quota_type';
SHOW COLUMNS FROM audit_logs LIKE 'operation_type';
```

dev / staging / prod 各确认一次。若某环境停在大写态（`g7h8i9j0k1l2`），需先 `alembic upgrade head` 再应用本修复——否则修复方向相反会弄坏。

### 3.2 方案 A（推荐）：共享 helper 收敛，统一修复

避免在每个 model 重复写 lambda，在 shared 层提供一个 helper：

```python
# src/shared/infrastructure/db_enum.py（新建）
from enum import Enum as PyEnum
from sqlalchemy import Enum as SAEnum

def lowercase_enum(enum_cls: type[PyEnum], **kw) -> SAEnum:
    """构造按 .value（小写）读写的 SQLAlchemy Enum 列类型。

    用于 DB ENUM 列定义为小写值、而 Python enum 成员名为大写的场景，
    避免 SQLAlchemy 默认按成员名读写导致的 LookupError。
    仅用于"名≠值且 DB 存小写值"的列；DB 存成员名的列（如 spaces）勿用。
    """
    return SAEnum(enum_cls, values_callable=lambda x: [e.value for e in x], **kw)
```

然后受影响的 10 列改用它，例如：

```python
# user_model.py
from src.shared.infrastructure.db_enum import lowercase_enum

status: Mapped[UserStatus] = mapped_column(lowercase_enum(UserStatus), ...)
role:   Mapped[UserRole]   = mapped_column(lowercase_enum(UserRole), ...)
auth_type: Mapped[AuthType] = mapped_column(lowercase_enum(AuthType), ...)
```

> 与 monitoring 现有的内联 `_enum_values` 等价；可顺手把 monitoring 也切到共享 helper 保持一致（可选，非必须）。

### 3.3 方案 B（保守）：逐列内联 values_callable

不引入共享 helper，每列照 monitoring 范式内联。改动更局部但有重复。若团队倾向最小改动可选此方案。

**推荐 A**：10 列分散在 3 模块，共享 helper 更 DRY，且为未来新增 enum 列提供正确默认。

### 3.4 audit 模块的特别处理

`audit_log_model.py` 用了独立的大写本地枚举（`ModelOperationType.CREATE="CREATE"`），且 docstring 声称"DB 是大写"——此假设已被迁移推翻。修复时：
- 确认 ORM 列用的本地枚举的 `.value` 与 DB 小写值一致（若本地枚举值是大写，需改用 `values_callable` 指向小写，或让本地枚举值改小写）。
- 更新 docstring 纠正"DB 是大写"的过时描述。
- 这一列的修复需比其他列更仔细核对，因为它绕了一层本地枚举映射。

---

## 4. 测试方案（堵 CI 盲区——本修复的核心价值）

bug 长期潜伏的根因是 CI 盲区：单测 mock session、集成测 mock service、唯一真实 DB 测（spaces）被跳过且测的是不受影响的模块。**只补 model 不补真实 DB 测，下次还会潜伏。**

### 4.1 为受影响模块补真实 DB repo 集成测试

参照 monitoring 的 `tests/integration/monitoring/test_repo_hyperpod_cluster.py` + `conftest.py`（真实 DB session fixture，无 mock）。为 auth / quotas / audit 各补 `test_repo_*.py`，覆盖：

```python
# 每个受影响 model 的核心断言：create → 真实 DB 读回 → enum 字段正确
async def test_create_and_read_back_preserves_enum(db_session):
    repo = UserRepositoryImpl(db_session)
    user = _make_user(status=UserStatus.ACTIVE, role=UserRole.ADMIN, auth_type=AuthType.LOCAL)
    created = await repo.create(user)
    fetched = await repo.get_by_id(created.id)   # 真实 DB 读回，修复前此处抛 LookupError
    assert fetched.status == UserStatus.ACTIVE
    assert fetched.role == UserRole.ADMIN
    assert fetched.auth_type == AuthType.LOCAL
```

优先级：auth（鉴权链路）> quotas > audit。

### 4.2 CI 必须能跑真实 DB

当前唯一真实 DB 测（spaces）在无 MySQL 时 `pytest.skip` → CI 无 MySQL 就静默跳过。**必须让 CI 提供 MySQL 服务**（GitHub Actions service container 或 testcontainers），否则补的测试照样被跳过，盲区依旧。这是堵盲区的前提。

### 4.3 架构防回归（可选增强）

加一个架构测试，扫描所有 ORM Enum 列：若其 Python enum 名≠值、且无 values_callable、且不在已知白名单（spaces 等 DB 存成员名的），则 fail——防止未来新增列重蹈覆辙。

---

## 5. 实施顺序建议

1. **前置**：核对 dev/staging/prod 的 `alembic_version` 与列定义大小写（§3.1）。
2. **CI 基建**：让 CI 跑真实 DB（§4.2）——否则后续测试无意义。
3. **auth 优先**（鉴权链路，TDD）：补 `test_repo_user.py` 真实 DB 测（红）→ user_model 三列加修复（绿）→ 真实环境验证登录/取用户。
4. **quotas**：同法补测 + 修 2 表 4 列。
5. **audit**：核对本地枚举 + 修 3 列 + 补测 + 纠正 docstring。
6. **架构防回归测试**（§4.3）。
7. 全量回归 + 各环境 `alembic upgrade head` 后部署验证。

---

## 6. 风险与注意

| 风险 | 应对 |
|------|------|
| 给 spaces 误加 values_callable | 严禁——spaces DB 存成员名，self-consistent（§2.2） |
| 生产 DB 大小写态与假设不符 | 修复前逐环境核对（§3.1），以真实列定义为准 |
| 修复后旧数据读不出 | 修复方向是让 SA 按小写 .value 读，与现小写 DB 列对齐；若某环境 DB 是大写，则该环境不应用此修复（先升级迁移） |
| audit 绕本地枚举层 | 单独仔细核对（§3.4） |
| CI 仍无 MySQL | 测试会被跳过，盲区不消除——§4.2 是硬前提 |

---

## 7. 验收标准

- [ ] auth/quotas/audit 10 列读写真实 DB 不抛 LookupError
- [ ] 各模块真实 DB repo 集成测试覆盖 create→读回 enum 往返，全绿
- [ ] CI 能跑真实 DB（MySQL service），上述测试不被跳过
- [ ] 真实环境登录/取用户/配额/审计写入路径验证正常
- [ ] spaces / datasets / models / training 未被误改（回归绿）
- [ ] （可选）架构防回归测试就位
