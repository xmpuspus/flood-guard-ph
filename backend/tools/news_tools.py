import json
import logging
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from backend.services.news_service import NewsService

logger = logging.getLogger(__name__)


class NewsFetchInput(BaseModel):
    """Input for news fetch tool"""

    query: str = Field(description="Search query for news")
    project_id: Optional[str] = Field(None, description="Related project ID")
    contractor: Optional[str] = Field(None, description="Related contractor name")


class NewsFetchTool(BaseTool):
    """Tool for fetching related news"""

    name: str = "news_fetch"
    description: str = """
    Fetch news articles related to projects, contractors, or locations.
    Use this when the user asks about news, media coverage, or recent developments.
    Returns relevant news articles with titles, sources, and links.
    """
    args_schema: type = NewsFetchInput
    news_service: NewsService

    def __init__(self, news_service: NewsService):
        super().__init__(news_service=news_service)

    async def _arun(
        self,
        query: str,
        project_id: Optional[str] = None,
        contractor: Optional[str] = None,
    ) -> str:
        """Fetch news articles"""
        try:
            articles = await self.news_service.search_news(
                query=query,
                project_id=project_id,
                contractor=contractor,
                n_results=5,
            )

            if len(articles) == 0:
                return "No related news articles found."

            news_data = []
            for article in articles:
                news_data.append(
                    {
                        "title": article.title,
                        "source": article.source,
                        "url": article.url,
                        "snippet": article.snippet,
                        "published": article.published_date,
                        "relevance": article.relevance_score,
                    }
                )

            return json.dumps(
                {"count": len(news_data), "articles": news_data}, indent=2
            )

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return f"Error fetching news: {str(e)}"

    def _run(
        self,
        query: str,
        project_id: Optional[str] = None,
        contractor: Optional[str] = None,
    ) -> str:
        """Synchronous version (not used in async context)"""
        return "This tool requires async execution"