"""Pagination Utilities - Common pagination calculations."""


def calculate_total_pages(total: int, page_size: int) -> int:
    """Calculate total pages for pagination.

    Args:
        total: Total number of items
        page_size: Number of items per page

    Returns:
        Total number of pages (0 if no items)
    """
    if total <= 0 or page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size


def calculate_offset(page: int, page_size: int) -> int:
    """Calculate offset for database queries.

    Args:
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Offset value for database query
    """
    return (max(1, page) - 1) * page_size
