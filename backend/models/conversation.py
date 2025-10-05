from typing import Any, Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Incoming chat message"""

    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Outgoing chat response"""

    type: Literal["status", "tool", "projects", "map_bounds", "message", "news"]
    content: Optional[str] = None
    data: Optional[Any] = None
    done: Optional[bool] = None
    count: Optional[int] = None
    tool: Optional[str] = None
    params: Optional[dict] = None
    bbox: Optional[list[list[float]]] = None


class NewsArticle(BaseModel):
    """News article model"""

    title: str
    snippet: str
    url: str
    source: str
    published_date: str
    relevance_score: float = 0.0