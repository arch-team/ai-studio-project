"""Settings 配置单元测试。"""

from src.shared.infrastructure.config import Settings


class TestSettingsAmpConfig:
    """AMP（Amazon Managed Prometheus）配置字段测试。"""

    def test_settings_has_amp_endpoint_default_none(self) -> None:
        """Settings 应包含 amp_query_endpoint 字段，默认 None。"""
        settings = Settings()

        assert hasattr(settings, "amp_query_endpoint")
        assert settings.amp_query_endpoint is None

    def test_settings_has_amp_region_default_us_east_1(self) -> None:
        """Settings 应包含 amp_region 字段，默认 us-east-1。"""
        settings = Settings()

        assert hasattr(settings, "amp_region")
        assert settings.amp_region == "us-east-1"
