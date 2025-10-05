import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.services.news_service import NewsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/news")
async def get_news(
    project_id: Optional[str] = Query(None),
    contractor: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
):
    """Get related news articles via web search"""
    try:
        # Get news service from app state
        from backend.main import news_service

        # Use project description as search query
        search_query = query or ""

        # Search news with web search
        articles = await news_service.search_news(
            query=search_query,
            project_id=project_id,
            contractor=contractor,
            location=location,
            n_results=5,
        )

        return {
            "articles": [article.dict() for article in articles],
            "count": len(articles),
        }

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))