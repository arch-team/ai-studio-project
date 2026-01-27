"""报表导出服务单元测试 - T078。

测试范围:
1. 资源使用报表 CSV 导出
2. 成本分析报表 CSV 导出
3. 列选择和日期格式化
4. 中文列名和 UTF-8 编码
5. 数值格式化 (货币、百分比)
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

from src.modules.billing.application.services.report_export_service import ReportExportService


class TestReportExportServiceCSVExport:
    """测试 CSV 导出功能。"""

    @pytest.fixture
    def service(self) -> ReportExportService:
        """创建服务实例。"""
        return ReportExportService()

    @pytest.fixture
    def sample_resource_usage_data(self) -> list[dict]:
        """示例资源使用数据。"""
        return [
            {
                "user_id": 1,
                "username": "user1",
                "total_gpu_hours": Decimal("100.5"),
                "total_cost_usd": Decimal("250.75"),
                "total_storage_bytes": 1024 * 1024 * 1024 * 10,  # 10 GB
                "total_training_jobs": 5,
                "created_at": datetime(2025, 1, 1, 10, 0, 0),
            },
            {
                "user_id": 2,
                "username": "user2",
                "total_gpu_hours": Decimal("50.25"),
                "total_cost_usd": Decimal("125.50"),
                "total_storage_bytes": 1024 * 1024 * 1024 * 5,  # 5 GB
                "total_training_jobs": 3,
                "created_at": datetime(2025, 1, 2, 15, 30, 0),
            },
        ]

    @pytest.fixture
    def sample_cost_analysis_data(self) -> list[dict]:
        """示例成本分析数据。"""
        return [
            {
                "period": "2025-01",
                "compute_cost": Decimal("1000.00"),
                "storage_cost": Decimal("50.00"),
                "network_cost": Decimal("20.00"),
                "total_cost": Decimal("1070.00"),
                "job_count": 10,
            },
            {
                "period": "2025-02",
                "compute_cost": Decimal("1200.00"),
                "storage_cost": Decimal("55.00"),
                "network_cost": Decimal("25.00"),
                "total_cost": Decimal("1280.00"),
                "job_count": 12,
            },
        ]

    def test_export_resource_usage_csv_basic(
        self, service: ReportExportService, sample_resource_usage_data: list[dict]
    ) -> None:
        """测试基本资源使用报表 CSV 导出。"""
        # Act
        csv_bytes = service.export_resource_usage_csv(sample_resource_usage_data)

        # Assert
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0

        # 验证 CSV 内容
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df) == 2
        assert "用户ID" in df.columns
        assert "用户名" in df.columns
        assert "总GPU时数" in df.columns
        assert "总成本(USD)" in df.columns

    def test_export_resource_usage_csv_with_column_selection(
        self, service: ReportExportService, sample_resource_usage_data: list[dict]
    ) -> None:
        """测试列选择功能。"""
        # Arrange
        selected_columns = ["user_id", "username", "total_gpu_hours"]

        # Act
        csv_bytes = service.export_resource_usage_csv(sample_resource_usage_data, columns=selected_columns)

        # Assert
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df.columns) == 3
        assert "用户ID" in df.columns
        assert "用户名" in df.columns
        assert "总GPU时数" in df.columns
        assert "总成本(USD)" not in df.columns

    def test_export_resource_usage_csv_with_date_formatting(
        self, service: ReportExportService, sample_resource_usage_data: list[dict]
    ) -> None:
        """测试日期格式化。"""
        # Act
        csv_bytes = service.export_resource_usage_csv(sample_resource_usage_data)

        # Assert
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        # 验证创建时间列存在且格式正确 (YYYY-MM-DD HH:MM:SS)
        assert "创建时间" in df.columns
        assert df["创建时间"].iloc[0] == "2025-01-01 10:00:00"

    def test_export_resource_usage_csv_with_numeric_formatting(
        self, service: ReportExportService, sample_resource_usage_data: list[dict]
    ) -> None:
        """测试数值格式化 (货币、存储容量)。"""
        # Act
        csv_bytes = service.export_resource_usage_csv(sample_resource_usage_data)

        # Assert - 直接检查 CSV 文本内容
        csv_text = csv_bytes.decode("utf-8")
        # 验证数值格式（保留 2 位小数）
        assert "100.50" in csv_text  # GPU 时数
        assert "$250.75" in csv_text  # 成本格式
        assert "10.00 GB" in csv_text  # 存储容量格式

    def test_export_resource_usage_csv_empty_data(self, service: ReportExportService) -> None:
        """测试空数据导出。"""
        # Act
        csv_bytes = service.export_resource_usage_csv([])

        # Assert
        assert isinstance(csv_bytes, bytes)
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df) == 0
        assert len(df.columns) > 0  # 列头应该存在

    def test_export_cost_analysis_csv_basic(
        self, service: ReportExportService, sample_cost_analysis_data: list[dict]
    ) -> None:
        """测试成本分析报表 CSV 导出。"""
        # Act
        csv_bytes = service.export_cost_analysis_csv(sample_cost_analysis_data)

        # Assert
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0

        # 验证 CSV 内容
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df) == 2
        assert "周期" in df.columns
        assert "计算成本" in df.columns
        assert "存储成本" in df.columns
        assert "网络成本" in df.columns
        assert "总成本" in df.columns

    def test_export_cost_analysis_csv_with_column_selection(
        self, service: ReportExportService, sample_cost_analysis_data: list[dict]
    ) -> None:
        """测试成本分析报表列选择。"""
        # Arrange
        selected_columns = ["period", "compute_cost", "total_cost"]

        # Act
        csv_bytes = service.export_cost_analysis_csv(sample_cost_analysis_data, columns=selected_columns)

        # Assert
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df.columns) == 3
        assert "周期" in df.columns
        assert "计算成本" in df.columns
        assert "总成本" in df.columns
        assert "存储成本" not in df.columns

    def test_export_cost_analysis_csv_with_currency_formatting(
        self, service: ReportExportService, sample_cost_analysis_data: list[dict]
    ) -> None:
        """测试货币格式化。"""
        # Act
        csv_bytes = service.export_cost_analysis_csv(sample_cost_analysis_data)

        # Assert
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        # 验证货币格式 ($ 符号 + 逗号分隔符)
        assert df["计算成本"].iloc[0] == "$1,000.00"
        assert df["总成本"].iloc[0] == "$1,070.00"

    def test_export_cost_analysis_csv_empty_data(self, service: ReportExportService) -> None:
        """测试空成本分析数据导出。"""
        # Act
        csv_bytes = service.export_cost_analysis_csv([])

        # Assert
        assert isinstance(csv_bytes, bytes)
        df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert len(df) == 0

    def test_csv_utf8_encoding(self, service: ReportExportService, sample_resource_usage_data: list[dict]) -> None:
        """测试 UTF-8 编码支持中文列名。"""
        # Act
        csv_bytes = service.export_resource_usage_csv(sample_resource_usage_data)

        # Assert - 能够正确解码中文
        csv_str = csv_bytes.decode("utf-8")
        assert "用户ID" in csv_str
        assert "总GPU时数" in csv_str
        assert "总成本" in csv_str
