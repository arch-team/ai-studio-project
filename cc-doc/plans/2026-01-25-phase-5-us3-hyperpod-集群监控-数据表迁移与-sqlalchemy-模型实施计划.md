# Phase 5 US3: HyperPod 集群监控 - 数据表迁移与 SQLAlchemy 模型实施计划

## 概述

**目标**: 实施 Phase 5 US3 (P1) 资源配额和集群监控的数据表迁移与 SQLAlchemy 模型

**任务范围**:
- T053: 创建 `hyperpod_clusters` 表迁移
- T054: 创建 `HyperPodCluster` 域实体和 ORM 模型

**开发流程**: TDD (测试驱动开发)

---

## 任务分解

### T053: 创建 hyperpod_clusters 表迁移

**文件**: `backend/alembic/versions/20260126_100000_create_hyperpod_clusters.py`

**迁移链**: `9a1b2c3d4e5f` (datasets) → 新迁移

**表结构** (来自 data-model.md):

```sql
CREATE TABLE hyperpod_clusters (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cluster_name VARCHAR(128) NOT NULL UNIQUE,
    cluster_arn VARCHAR(512) NOT NULL UNIQUE,
    region VARCHAR(32) NOT NULL,
    vpc_id VARCHAR(64) NOT NULL,
    instance_groups JSON NOT NULL,
    total_nodes INT UNSIGNED NOT NULL,
    available_nodes INT UNSIGNED DEFAULT 0,
    total_cpu_cores INT UNSIGNED,
    total_gpu_count INT UNSIGNED,
    total_memory_gb INT UNSIGNED,
    status ENUM('creating', 'active', 'updating', 'deleting', 'failed') NOT NULL DEFAULT 'creating',
    health_status ENUM('healthy', 'degraded', 'unhealthy'),
    fsx_filesystem_id VARCHAR(128),
    fsx_mount_point VARCHAR(256),
    prometheus_endpoint VARCHAR(512),
    grafana_workspace_id VARCHAR(128),
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    last_sync_at DATETIME(3),
    INDEX idx_region (region),
    INDEX idx_status (status),
    INDEX idx_health_status (health_status)
);
```

**TDD 步骤**:
1. 编写迁移文件
2. 运行 `alembic upgrade head` 验证
3. 运行 `alembic downgrade -1` 验证回滚

---

### T054: 创建 HyperPodCluster 模型

#### T054.1: 创建值对象（枚举）

**文件**: `backend/src/modules/monitoring/domain/value_objects/cluster_enums.py`

**内容**:
```python
from enum import Enum

class ClusterStatus(Enum):
    """HyperPod 集群状态"""
    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    DELETING = "deleting"
    FAILED = "failed"

class HealthStatus(Enum):
    """集群健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

# 状态转换规则
CLUSTER_STATUS_TRANSITIONS: dict[ClusterStatus, set[ClusterStatus]] = {
    ClusterStatus.CREATING: {ClusterStatus.ACTIVE, ClusterStatus.FAILED},
    ClusterStatus.ACTIVE: {ClusterStatus.UPDATING, ClusterStatus.DELETING},
    ClusterStatus.UPDATING: {ClusterStatus.ACTIVE, ClusterStatus.FAILED},
    ClusterStatus.DELETING: {ClusterStatus.FAILED},  # 删除完成后记录被移除
    ClusterStatus.FAILED: {ClusterStatus.CREATING},  # 可重试
}
```

**TDD 步骤**:
1. ✅ 先写测试: `backend/tests/unit/modules/monitoring/domain/test_vo_cluster_enums.py`
2. 再写实现: `cluster_enums.py`
3. 运行测试验证

#### T054.2: 创建域实体

**文件**: `backend/src/modules/monitoring/domain/entities/hyperpod_cluster.py`

**关键设计**:
- 使用 `@dataclass` 定义
- 状态转换方法 `can_transition_to()`, `transition_to()`
- 便捷检查方法 `is_active()`, `is_healthy()`
- 资源统计属性 `gpu_utilization`, `node_utilization`

**TDD 步骤**:
1. ✅ 先写测试: `backend/tests/unit/modules/monitoring/domain/test_entity_hyperpod_cluster.py`
2. 再写实现: `hyperpod_cluster.py`
3. 运行测试验证

#### T054.3: 创建 ORM 模型

**文件**: `backend/src/modules/monitoring/infrastructure/models/hyperpod_cluster_model.py`

**关键设计**:
- 继承 `Base, TimestampMixin`
- 枚举字段使用 `Mapped[ClusterStatus]` + `Enum(ClusterStatus)`
- JSON 字段使用 `Mapped[list | dict]` + `mysql.JSON()`
- 时间戳字段使用 `server_default`

**TDD 步骤**:
1. ORM 模型不需要单独的单元测试（由集成测试覆盖）
2. 验证迁移后模型可正常映射

---

## 文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `backend/alembic/versions/20260126_100000_create_hyperpod_clusters.py` | 数据库迁移 |
| `backend/src/modules/monitoring/domain/value_objects/cluster_enums.py` | 枚举值对象 |
| `backend/src/modules/monitoring/domain/entities/hyperpod_cluster.py` | 域实体 |
| `backend/src/modules/monitoring/infrastructure/models/hyperpod_cluster_model.py` | ORM 模型 |
| `backend/tests/unit/modules/monitoring/__init__.py` | 测试包初始化 |
| `backend/tests/unit/modules/monitoring/domain/__init__.py` | 域测试包初始化 |
| `backend/tests/unit/modules/monitoring/domain/test_vo_cluster_enums.py` | 枚举测试 |
| `backend/tests/unit/modules/monitoring/domain/test_entity_hyperpod_cluster.py` | 实体测试 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `backend/src/modules/monitoring/domain/value_objects/__init__.py` | 导出枚举 |
| `backend/src/modules/monitoring/domain/entities/__init__.py` | 导出实体 |
| `backend/src/modules/monitoring/infrastructure/models/__init__.py` | 导出 ORM 模型 |

---

## 执行顺序

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 值对象 (TDD)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1.1 编写 test_vo_cluster_enums.py (RED)                 │   │
│  │ 1.2 实现 cluster_enums.py (GREEN)                       │   │
│  │ 1.3 更新 value_objects/__init__.py                      │   │
│  │ 1.4 运行测试验证 ✅                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: 域实体 (TDD)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.1 编写 test_entity_hyperpod_cluster.py (RED)          │   │
│  │ 2.2 实现 hyperpod_cluster.py (GREEN)                    │   │
│  │ 2.3 更新 entities/__init__.py                           │   │
│  │ 2.4 运行测试验证 ✅                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: 数据库迁移                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 3.1 创建迁移文件 20260126_100000_create_hyperpod_...    │   │
│  │ 3.2 运行 alembic upgrade head 验证                      │   │
│  │ 3.3 运行 alembic downgrade -1 验证回滚                  │   │
│  │ 3.4 重新 upgrade head ✅                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: ORM 模型                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 4.1 实现 hyperpod_cluster_model.py                      │   │
│  │ 4.2 更新 models/__init__.py                             │   │
│  │ 4.3 验证模型与迁移一致性 ✅                              │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: 最终验证                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 5.1 运行全部单元测试 pytest tests/unit/modules/monitoring │   │
│  │ 5.2 运行代码质量检查 black + ruff + mypy                │   │
│  │ 5.3 更新 tasks.md 标记完成状态                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 测试用例设计

### test_vo_cluster_enums.py

```python
class TestClusterStatusEnum:
    """ClusterStatus 枚举测试"""
    def test_all_statuses_defined(self) -> None:
        """验证所有必需状态已定义"""

    def test_status_values_match_database(self) -> None:
        """验证枚举值与数据库 ENUM 一致"""

class TestHealthStatusEnum:
    """HealthStatus 枚举测试"""
    def test_all_health_statuses_defined(self) -> None:
        """验证所有健康状态已定义"""

class TestClusterStatusTransitions:
    """状态转换规则测试"""
    def test_creating_can_transition_to_active(self) -> None:
        """creating → active 是有效转换"""

    def test_creating_can_transition_to_failed(self) -> None:
        """creating → failed 是有效转换"""

    def test_active_cannot_transition_to_creating(self) -> None:
        """active → creating 是无效转换"""
```

### test_entity_hyperpod_cluster.py

```python
class TestHyperPodClusterCreation:
    """HyperPodCluster 实体创建测试"""
    def test_create_with_required_fields(self) -> None:
        """使用必填字段创建集群"""

    def test_default_status_is_creating(self) -> None:
        """默认状态为 creating"""

    def test_default_available_nodes_is_zero(self) -> None:
        """默认可用节点数为 0"""

class TestHyperPodClusterStateTransitions:
    """状态转换测试"""
    def test_can_transition_to_active_from_creating(self) -> None:
        """从 creating 可转换到 active"""

    def test_cannot_transition_to_creating_from_active(self) -> None:
        """从 active 不能转换到 creating"""

    def test_transition_updates_timestamp(self) -> None:
        """状态转换更新 updated_at"""

class TestHyperPodClusterUtilizationMethods:
    """资源利用率方法测试"""
    def test_node_utilization_calculation(self) -> None:
        """节点利用率计算"""

    def test_node_utilization_zero_when_no_total(self) -> None:
        """总节点为 0 时利用率为 0"""

class TestHyperPodClusterHealthChecks:
    """健康检查方法测试"""
    def test_is_healthy_returns_true(self) -> None:
        """健康状态检查"""

    def test_is_active_returns_true(self) -> None:
        """活跃状态检查"""
```

---

## 验收标准

- [ ] 所有测试通过 (`pytest tests/unit/modules/monitoring -v`)
- [ ] 迁移可正常应用和回滚
- [ ] 代码通过质量检查 (`black`, `ruff`, `mypy`)
- [ ] 枚举值与 data-model.md 中定义一致
- [ ] 实体方法覆盖状态转换、资源计算、健康检查
- [ ] ORM 模型字段与迁移文件一致
- [ ] tasks.md 中 T053、T054 标记为完成

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 迁移与现有数据冲突 | 开发环境无数据，生产部署前需备份 |
| 枚举值与 HyperPod API 不匹配 | 参考 AWS 文档确认状态值 |
| 时间戳精度问题 | MySQL 使用 DATETIME(3) 支持毫秒 |

---

## 命令参考

```bash
# 运行单元测试
pytest tests/unit/modules/monitoring -v

# 运行特定测试
pytest tests/unit/modules/monitoring/domain/test_vo_cluster_enums.py -v

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 代码质量检查
black backend/src/modules/monitoring backend/tests/unit/modules/monitoring
ruff check backend/src/modules/monitoring backend/tests/unit/modules/monitoring
mypy backend/src/modules/monitoring
```
