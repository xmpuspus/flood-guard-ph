"""Pagination models for API responses

Enhancement #10: Implement Pagination
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for requests"""
    offset: int = Field(0, ge=0, le=100000, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items per page")
    cursor: Optional[str] = Field(None, max_length=200, description="Cursor for cursor-based pagination")

    def get_page_number(self) -> int:
        """Calculate page number from offset/limit"""
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response with metadata"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None
    ):
        """Create paginated response with calculated metadata"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )
