"""JobTemplate domain entity for reusable training configurations."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.utils import utc_now

from ..value_objects import TemplateVisibility


@dataclass
class JobTemplate:
    """Job template domain entity for reusable training configurations."""

    # === Required fields ===
    id: int
    name: str
    owner_id: int
    training_config: dict

    # === Optional fields ===
    description: str | None = None
    visibility: TemplateVisibility = TemplateVisibility.PRIVATE

    # === Usage statistics ===
    usage_count: int = 0
    last_used_at: datetime | None = None

    # === Audit fields ===
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    deleted_at: datetime | None = None

    def is_visible_to(self, user_id: int) -> bool:
        """Check if the template is visible to a given user.

        - PUBLIC templates are visible to everyone
        - PRIVATE/TEAM templates are only visible to the owner
        """
        if self.visibility == TemplateVisibility.PUBLIC:
            return True
        # For PRIVATE and TEAM, only owner can see
        # (TEAM visibility would require team membership check in service layer)
        return self.owner_id == user_id

    def can_modify(self, user_id: int) -> bool:
        """Check if the user can modify this template."""
        return self.owner_id == user_id

    def increment_usage(self) -> None:
        """Increment usage count and update last_used_at."""
        self.usage_count += 1
        self.last_used_at = utc_now()
        self.updated_at = utc_now()

    def is_deleted(self) -> bool:
        """Check if template is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft delete the template."""
        self.deleted_at = utc_now()
        self.updated_at = utc_now()

    def update_name(self, name: str) -> None:
        """Update template name."""
        self.name = name
        self.updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        """Update template description."""
        self.description = description
        self.updated_at = utc_now()

    def update_visibility(self, visibility: TemplateVisibility) -> None:
        """Update template visibility."""
        self.visibility = visibility
        self.updated_at = utc_now()

    def update_training_config(self, training_config: dict) -> None:
        """Update training configuration."""
        self.training_config = training_config
        self.updated_at = utc_now()
