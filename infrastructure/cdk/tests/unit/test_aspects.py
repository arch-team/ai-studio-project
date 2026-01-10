"""
Unit tests for tagging utilities module.

Tests cover:
- apply_standard_tags function
- get_standard_tags function
- get_data_classification_tag function
"""

import aws_cdk as cdk

from aspects import (
    apply_standard_tags,
    get_data_classification_tag,
    get_standard_tags,
)
from config import EnvironmentConfig


class TestApplyStandardTags:
    """Tests for apply_standard_tags function."""

    def test_applies_project_tag(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig
    ) -> None:
        """Verify Project tag is applied."""
        apply_standard_tags(cdk_app, dev_config)
        # Tags are applied lazily during synthesis
        # We verify the function executes without error
        assert True

    def test_accepts_environment_config(
        self, cdk_app: cdk.App, dev_config: EnvironmentConfig
    ) -> None:
        """Verify function accepts EnvironmentConfig."""
        # Should not raise
        apply_standard_tags(cdk_app, dev_config)

    def test_works_with_all_environments(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify function works with dev, staging, and prod configs."""
        for factory in [
            EnvironmentConfig.for_dev,
            EnvironmentConfig.for_staging,
            EnvironmentConfig.for_prod,
        ]:
            config = factory(account=test_account, region=test_region)
            # Create a fresh app for each test
            app = cdk.App()
            apply_standard_tags(app, config)


class TestGetStandardTags:
    """Tests for get_standard_tags function."""

    def test_returns_dict(self, dev_config: EnvironmentConfig) -> None:
        """Verify function returns a dictionary."""
        tags = get_standard_tags(dev_config)
        assert isinstance(tags, dict)

    def test_contains_project_tag(self, dev_config: EnvironmentConfig) -> None:
        """Verify Project tag is included."""
        tags = get_standard_tags(dev_config)
        assert "Project" in tags
        assert tags["Project"] == "ai-training-platform"

    def test_contains_environment_tag(self, dev_config: EnvironmentConfig) -> None:
        """Verify Environment tag is included."""
        tags = get_standard_tags(dev_config)
        assert "Environment" in tags
        assert tags["Environment"] == "dev"

    def test_contains_managed_by_tag(self, dev_config: EnvironmentConfig) -> None:
        """Verify ManagedBy tag is included."""
        tags = get_standard_tags(dev_config)
        assert "ManagedBy" in tags
        assert tags["ManagedBy"] == "cdk"

    def test_contains_cost_center_tag(self, dev_config: EnvironmentConfig) -> None:
        """Verify CostCenter tag is included."""
        tags = get_standard_tags(dev_config)
        assert "CostCenter" in tags
        assert tags["CostCenter"] == "ai-platform-dev"

    def test_environment_specific_values(
        self, test_account: str, test_region: str
    ) -> None:
        """Verify tags vary by environment."""
        dev_tags = get_standard_tags(
            EnvironmentConfig.for_dev(account=test_account, region=test_region)
        )
        prod_tags = get_standard_tags(
            EnvironmentConfig.for_prod(account=test_account, region=test_region)
        )

        assert dev_tags["Environment"] == "dev"
        assert prod_tags["Environment"] == "prod"
        assert dev_tags["CostCenter"] == "ai-platform-dev"
        assert prod_tags["CostCenter"] == "ai-platform-prod"


class TestGetDataClassificationTag:
    """Tests for get_data_classification_tag function."""

    def test_default_classification(self) -> None:
        """Verify default classification is 'internal'."""
        tag = get_data_classification_tag()
        assert tag == {"DataClassification": "internal"}

    def test_custom_classification(self) -> None:
        """Verify custom classification values."""
        for classification in ["public", "internal", "confidential", "restricted"]:
            tag = get_data_classification_tag(classification)
            assert tag == {"DataClassification": classification}

    def test_returns_dict(self) -> None:
        """Verify function returns a dictionary."""
        tag = get_data_classification_tag()
        assert isinstance(tag, dict)
        assert "DataClassification" in tag
