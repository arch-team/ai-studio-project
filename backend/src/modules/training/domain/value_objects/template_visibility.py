"""Template visibility enum for job templates."""

from enum import Enum


class TemplateVisibility(Enum):
    """Template visibility scope for job templates."""

    PRIVATE = "PRIVATE"  # 仅所有者可见
    TEAM = "TEAM"  # 团队成员可见
    PUBLIC = "PUBLIC"  # 所有人可见
