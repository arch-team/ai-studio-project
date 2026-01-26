"""JobTemplate domain entity for reusable training configurations."""

from datetime import datetime

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.utils import utc_now

from ..value_objects import TemplateVisibility


class JobTemplate(PydanticEntity):
    """Job template domain entity for reusable training configurations."""

    # === Required fields ===
    name: str = Field(min_length=1, max_length=255)
    owner_id: int
    training_config: dict

    # === Optional fields ===
    description: str | None = None
    visibility: TemplateVisibility = TemplateVisibility.PRIVATE

    # === Usage statistics ===
    usage_count: int = 0
    last_used_at: datetime | None = None

    # === Audit fields ===
    deleted_at: datetime | None = None

    # ========== 业务方法 ==========

    def is_visible_to(self, user_id: int) -> bool:
        """Check if the template is visible to a given user."""
        if self.visibility == TemplateVisibility.PUBLIC:
            return True
        return self.owner_id == user_id

    def can_modify(self, user_id: int) -> bool:
        """Check if the user can modify this template."""
        return self.owner_id == user_id

    def increment_usage(self) -> None:
        """Increment usage count and update last_used_at."""
        self.usage_count += 1
        self.last_used_at = utc_now()
        self.touch()

    def is_deleted(self) -> bool:
        """Check if template is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft delete the template."""
        self.deleted_at = utc_now()
        self.touch()

    def update_name(self, name: str) -> None:
        """Update template name."""
        self.name = name
        self.touch()

    def update_description(self, description: str | None) -> None:
        """Update template description."""
        self.description = description
        self.touch()

    def update_visibility(self, visibility: TemplateVisibility) -> None:
        """Update template visibility."""
        self.visibility = visibility
        self.touch()

    def update_training_config(self, training_config: dict) -> None:
        """Update training configuration."""
        self.training_config = training_config
        self.touch()
