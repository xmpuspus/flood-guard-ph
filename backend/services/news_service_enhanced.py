"""Enhanced News Service with reliability improvements

Enhancement #17: Improve News Service Reliability
"""
import aiohttp
import asyncio
import feedparser
import logging
from typing import List, Optional
from datetime import datetime, timedelta

from backend.models.conversation import NewsArticle

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for failing services"""

    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception(f"Circuit breaker is OPEN (failure count: {self.failure_count})")

        try:
            result = await func()
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed - service recovered")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

            raise


class EnhancedNewsService:
    """
    Enhanced news service with reliability improvements

    Features:
    - Circuit breaker pattern
    - Retry with exponential backoff
    - Multiple news sources (8 sources)
    - Timeout handling
    - Deduplication
    """

    # Expanded news sources
    NEWS_SOURCES = [
        # RSS Feeds
        {"type": "rss", "url": "https://www.rappler.com/feed/", "name": "Rappler"},
        {"type": "rss", "url": "https://www.philstar.com/rss/headlines", "name": "PhilStar"},
        {"type": "rss", "url": "https://newsinfo.inquirer.net/feed", "name": "Inquirer"},
        {"type": "rss", "url": "https://pia.gov.ph/feed", "name": "PIA"},
        {"type": "rss", "url": "https://www.pna.gov.ph/rss/latest", "name": "PNA"},
        {"type": "rss", "url": "https://mb.com.ph/feed/", "name": "Manila Bulletin"},
        {"type": "rss", "url": "https://www.gmanetwork.com/news/rss/", "name": "GMA News"},
        {"type": "rss", "url": "https://news.abs-cbn.com/rss", "name": "ABS-CBN News"},
    ]

    def __init__(self, vector_service=None):
        self.vector_service = vector_service
        self.circuit_breakers = {
            source["url"]: CircuitBreaker() for source in self.NEWS_SOURCES
        }
        self.timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout

    async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch URL with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.warning(f"HTTP {response.status} from {url}")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")

            # Exponential backoff: 1s, 2s, 4s
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        return None

    async def search_news(self, query: str, n_results: int = 5) -> List[NewsArticle]:
        """Search news with fallback strategies"""
        try:
            # Try vector search first (fastest) if available
            if self.vector_service:
                vector_results = await self._vector_search(query, n_results)
                if len(vector_results) >= n_results:
                    return vector_results

            # Fallback: Fetch from RSS feeds
            rss_results = await self._fetch_from_rss(query, n_results)

            # Combine and deduplicate
            all_results = rss_results
            unique_results = self._deduplicate(all_results)

            return unique_results[:n_results]

        except Exception as e:
            logger.error(f"Error in search_news: {e}")
            return []

    async def _fetch_from_rss(self, query: str, n_results: int) -> List[NewsArticle]:
        """Fetch from multiple RSS feeds concurrently"""
        tasks = []
        for source in self.NEWS_SOURCES:
            if source["type"] == "rss":
                task = self._fetch_single_source(source, query)
                tasks.append(task)

        # Fetch all concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=15.0  # 15 second total timeout for all feeds
            )
        except asyncio.TimeoutError:
            logger.warning("RSS feed fetching timed out after 15s")
            return []

        # Filter out failures and flatten
        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)

        # Sort by relevance
        articles.sort(key=lambda x: x.relevance_score if hasattr(x, 'relevance_score') else 0, reverse=True)

        return articles[:n_results]

    async def _fetch_single_source(self, source: dict, query: str) -> List[NewsArticle]:
        """Fetch from single source with circuit breaker"""
        circuit_breaker = self.circuit_breakers[source["url"]]

        try:
            async def fetch():
                content = await self.fetch_with_retry(source["url"], max_retries=2)
                if not content:
                    return []

                # Parse RSS
                articles = self._parse_rss(content, source["name"])

                # Filter by query relevance
                relevant = self._filter_by_relevance(articles, query)

                return relevant

            return await circuit_breaker.call(fetch)

        except Exception as e:
            logger.debug(f"Circuit breaker blocked or error from {source['name']}: {e}")
            return []

    def _parse_rss(self, content: str, source_name: str) -> List[NewsArticle]:
        """Parse RSS feed content"""
        try:
            feed = feedparser.parse(content)
            articles = []

            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    article = NewsArticle(
                        title=entry.get('title', ''),
                        url=entry.get('link', ''),
                        snippet=entry.get('summary', '')[:300],
                        source=source_name,
                        published_date=entry.get('published', ''),
                        relevance_score=0.5  # Will be updated by relevance filter
                    )
                    articles.append(article)
                except Exception as e:
                    logger.debug(f"Error parsing entry from {source_name}: {e}")
                    continue

            return articles

        except Exception as e:
            logger.error(f"Error parsing RSS from {source_name}: {e}")
            return []

    def _filter_by_relevance(self, articles: List[NewsArticle], query: str) -> List[NewsArticle]:
        """Score articles by relevance to query"""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        for article in articles:
            try:
                text = (article.title + " " + article.snippet).lower()
                text_terms = set(text.split())

                # Simple relevance scoring
                common_terms = query_terms & text_terms
                score = len(common_terms) / len(query_terms) if query_terms else 0

                article.relevance_score = score
            except:
                article.relevance_score = 0.0

        # Filter out low relevance (< 0.1)
        return [a for a in articles if a.relevance_score > 0.1]

    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles by URL"""
        seen_urls = set()
        unique = []

        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique.append(article)

        return unique

    async def _vector_search(self, query: str, n_results: int) -> List[NewsArticle]:
        """Fallback to vector search if available"""
        if not self.vector_service:
            return []

        try:
            results = self.vector_service.search_news(query, n_results=n_results)
            articles = []

            for result in results:
                article = NewsArticle(
                    title=result.get('title', ''),
                    url=result.get('url', ''),
                    snippet=result.get('snippet', ''),
                    source=result.get('source', ''),
                    published_date='',
                    relevance_score=result.get('relevance_score', 0.5)
                )
                articles.append(article)

            return articles

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
