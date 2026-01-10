"""
Tagging utilities for AI Training Platform CDK Stacks.

This module exports functions for centralized tag management.

Usage:
    from aspects import apply_standard_tags, get_standard_tags

    # Apply standard tags to all resources in app
    apply_standard_tags(app, env_config)

    # Get tags as dictionary for manual use
    tags = get_standard_tags(env_config)
"""

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
