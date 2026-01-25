"""测试 UploadSessionModel ORM 模型。"""

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import inspect


class TestUploadSessionModelTableDefinition:
    """测试 UploadSessionModel 表定义。"""

    def test_table_name(self) -> None:
        """验证表名为 upload_sessions。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        assert UploadSessionModel.__tablename__ == "upload_sessions"

    def test_primary_key_is_id(self) -> None:
        """验证主键字段为 id。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        pk_columns = [col.name for col in mapper.primary_key]
        assert pk_columns == ["id"]

    def test_required_columns_exist(self) -> None:
        """验证必填列存在。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        column_names = [col.name for col in mapper.columns]

        required_columns = [
            "id",
            "upload_id",
            "dataset_id",
            "bucket",
            "s3_key",
            "filename",
            "content_type",
            "total_size",
            "part_size",
            "status",
            "owner_id",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in column_names, f"缺少必填列: {col}"

    def test_optional_columns_exist(self) -> None:
        """验证可选列存在。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        column_names = [col.name for col in mapper.columns]

        optional_columns = [
            "completed_parts",
            "uploaded_bytes",
            "completed_part_count",
            "expires_at",
        ]

        for col in optional_columns:
            assert col in column_names, f"缺少可选列: {col}"


class TestUploadSessionModelColumnTypes:
    """测试 UploadSessionModel 列类型。"""

    def test_id_is_bigint(self) -> None:
        """验证 id 为 BigInteger 类型。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        id_col = mapper.columns["id"]
        assert "BIGINT" in str(id_col.type).upper()

    def test_upload_id_is_string(self) -> None:
        """验证 upload_id 为 String 类型。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["upload_id"]
        assert (
            "VARCHAR" in str(col.type).upper()
            or "STRING" in str(col.type).upper()
        )

    def test_total_size_is_bigint(self) -> None:
        """验证 total_size 为 BigInteger 类型。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["total_size"]
        assert "BIGINT" in str(col.type).upper()

    def test_status_is_enum(self) -> None:
        """验证 status 为 Enum 类型。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["status"]
        assert isinstance(col.type, SQLEnum)

    def test_completed_parts_is_json(self) -> None:
        """验证 completed_parts 为 JSON 类型。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["completed_parts"]
        assert "JSON" in str(col.type).upper()


class TestUploadSessionModelRelationships:
    """测试 UploadSessionModel 关系。"""

    def test_has_dataset_relationship(self) -> None:
        """验证有 dataset 关系。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        relationships = {rel.key for rel in mapper.relationships}
        assert "dataset" in relationships

    def test_has_owner_relationship(self) -> None:
        """验证有 owner 关系。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        relationships = {rel.key for rel in mapper.relationships}
        assert "owner" in relationships

    def test_dataset_id_is_foreign_key(self) -> None:
        """验证 dataset_id 为外键。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        dataset_id_col = mapper.columns["dataset_id"]
        assert len(dataset_id_col.foreign_keys) > 0

    def test_owner_id_is_foreign_key(self) -> None:
        """验证 owner_id 为外键。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        owner_id_col = mapper.columns["owner_id"]
        assert len(owner_id_col.foreign_keys) > 0


class TestUploadSessionModelDefaults:
    """测试 UploadSessionModel 默认值。"""

    def test_status_default_is_initiated(self) -> None:
        """验证 status 默认值为 INITIATED。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        status_col = mapper.columns["status"]
        assert status_col.default is not None or status_col.server_default is not None

    def test_uploaded_bytes_default_is_zero(self) -> None:
        """验证 uploaded_bytes 默认值为 0。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["uploaded_bytes"]
        assert col.default is not None or col.server_default is not None

    def test_completed_part_count_default_is_zero(self) -> None:
        """验证 completed_part_count 默认值为 0。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)
        col = mapper.columns["completed_part_count"]
        assert col.default is not None or col.server_default is not None


class TestUploadSessionModelNullability:
    """测试 UploadSessionModel 列的可空性。"""

    def test_required_columns_not_nullable(self) -> None:
        """验证必填列不可为空。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)

        not_nullable_columns = [
            "id",
            "upload_id",
            "dataset_id",
            "bucket",
            "s3_key",
            "filename",
            "total_size",
            "part_size",
            "status",
            "owner_id",
        ]

        for col_name in not_nullable_columns:
            col = mapper.columns[col_name]
            assert col.nullable is False, f"列 {col_name} 应该不可为空"

    def test_optional_columns_nullable(self) -> None:
        """验证可选列可为空。"""
        from src.modules.datasets.infrastructure.models import UploadSessionModel

        mapper = inspect(UploadSessionModel)

        nullable_columns = [
            "completed_parts",
            "expires_at",
        ]

        for col_name in nullable_columns:
            col = mapper.columns[col_name]
            assert col.nullable is True, f"列 {col_name} 应该可为空"
