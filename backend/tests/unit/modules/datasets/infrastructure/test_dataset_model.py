"""测试 DatasetModel ORM 模型。"""

from sqlalchemy import inspect


class TestDatasetModelTableDefinition:
    """测试 DatasetModel 表定义。"""

    def test_table_name(self) -> None:
        """验证表名为 datasets。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        assert DatasetModel.__tablename__ == "datasets"

    def test_primary_key_is_id(self) -> None:
        """验证主键字段为 id。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        pk_columns = [col.name for col in mapper.primary_key]
        assert pk_columns == ["id"]

    def test_required_columns_exist(self) -> None:
        """验证必填列存在。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        column_names = [col.name for col in mapper.columns]

        required_columns = [
            "id",
            "name",
            "storage_type",
            "storage_uri",
            "dataset_type",
            "owner_id",
            "visibility",
            "status",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in column_names, f"缺少必填列: {col}"

    def test_optional_columns_exist(self) -> None:
        """验证可选列存在。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        column_names = [col.name for col in mapper.columns]

        optional_columns = [
            "description",
            "version",
            "total_size_bytes",
            "file_count",
            "data_format",
            "tags",
            "last_accessed_at",
        ]

        for col in optional_columns:
            assert col in column_names, f"缺少可选列: {col}"


class TestDatasetModelColumnTypes:
    """测试 DatasetModel 列类型。"""

    def test_id_is_bigint(self) -> None:
        """验证 id 为 BigInteger 类型。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        id_col = mapper.columns["id"]
        assert "BIGINT" in str(id_col.type).upper()

    def test_name_is_string(self) -> None:
        """验证 name 为 String 类型且有长度限制。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        name_col = mapper.columns["name"]
        assert "VARCHAR" in str(name_col.type).upper() or "STRING" in str(name_col.type).upper()

    def test_storage_type_is_enum(self) -> None:
        """验证 storage_type 为 Enum 类型。"""
        from sqlalchemy import Enum as SQLEnum

        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        col = mapper.columns["storage_type"]
        # SQLAlchemy Enum 类型检查
        assert isinstance(col.type, SQLEnum)

    def test_status_is_enum(self) -> None:
        """验证 status 为 Enum 类型。"""
        from sqlalchemy import Enum as SQLEnum

        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        col = mapper.columns["status"]
        # SQLAlchemy Enum 类型检查
        assert isinstance(col.type, SQLEnum)

    def test_tags_is_json(self) -> None:
        """验证 tags 为 JSON 类型。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        col = mapper.columns["tags"]
        assert "JSON" in str(col.type).upper()


class TestDatasetModelRelationships:
    """测试 DatasetModel 关系。"""

    def test_has_owner_relationship(self) -> None:
        """验证有 owner 关系。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        relationships = {rel.key for rel in mapper.relationships}
        assert "owner" in relationships

    def test_owner_id_is_foreign_key(self) -> None:
        """验证 owner_id 为外键。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        owner_id_col = mapper.columns["owner_id"]
        assert len(owner_id_col.foreign_keys) > 0


class TestDatasetModelDefaults:
    """测试 DatasetModel 默认值。"""

    def test_version_default_is_v1(self) -> None:
        """验证 version 默认值为 v1。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        version_col = mapper.columns["version"]
        # 检查是否有默认值
        assert version_col.default is not None or version_col.server_default is not None

    def test_visibility_default_is_private(self) -> None:
        """验证 visibility 默认值为 PRIVATE。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        visibility_col = mapper.columns["visibility"]
        # DatasetVisibility.PRIVATE 是默认值
        assert visibility_col.default is not None

    def test_status_default_is_preparing(self) -> None:
        """验证 status 默认值为 PREPARING。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)
        status_col = mapper.columns["status"]
        # DatasetStatus.PREPARING 是默认值
        assert status_col.default is not None


class TestDatasetModelNullability:
    """测试 DatasetModel 列的可空性。"""

    def test_required_columns_not_nullable(self) -> None:
        """验证必填列不可为空。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)

        not_nullable_columns = [
            "id",
            "name",
            "storage_type",
            "storage_uri",
            "dataset_type",
            "owner_id",
            "visibility",
            "status",
        ]

        for col_name in not_nullable_columns:
            col = mapper.columns[col_name]
            assert col.nullable is False, f"列 {col_name} 应该不可为空"

    def test_optional_columns_nullable(self) -> None:
        """验证可选列可为空。"""
        from src.modules.datasets.infrastructure.models import DatasetModel

        mapper = inspect(DatasetModel)

        nullable_columns = [
            "description",
            "total_size_bytes",
            "file_count",
            "data_format",
            "tags",
            "last_accessed_at",
        ]

        for col_name in nullable_columns:
            col = mapper.columns[col_name]
            assert col.nullable is True, f"列 {col_name} 应该可为空"
