"""App 级别全局标签管理。"""

from .tagging import (
    apply_standard_tags,
    get_data_classification_tag,
    get_standard_tags,
)

__all__ = [
    "apply_standard_tags",
    "get_data_classification_tag",
    "get_standard_tags",
]
