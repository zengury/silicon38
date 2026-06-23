"""
Application-layer DTOs (Data Transfer Objects).

These are plain Python objects used to transfer data between layers
without coupling to SQLModel/SQLAlchemy internals.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class PageResult:
    """Generic paginated response wrapper.

    Attributes:
        total: Total number of records matching the query.
        items: List of items for the current page.
    """

    def __init__(
        self,
        total: int = 0,
        items: List[Any] = None,
    ) -> None:
        self.total = total
        self.items = items or []
