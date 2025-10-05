import hashlib
import logging
import re
from datetime import datetime
from typing import Optional

import aiohttp
import feedparser

from backend.config import settings
from backend.models.conversation import NewsArticle

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and searching news"""

    def __init__(self, vector_service):
        self.vector_service = vector_service
        self.rss_feeds = [
            "https://www.rappler.com/feed/",
            "https://www.philstar.com/rss/headlines",
            "https://newsinfo.inquirer.net/feed",
        ]

    async def search_news(
        self,
        query: str,
        project_id: Optional[str] = None,
        contractor: Optional[str] = None,
        location: Optional[str] = None,
        n_results: int = 5,
    ) -> list[NewsArticle]:
        """Search for related news articles using web search"""
        try:
            # Build comprehensive search query for Philippine flood control news
            search_terms = []
            
            # Add core context
            search_terms.append("Philippines flood control")
            
            # Add project description (cleaned)
            if query and query != "flood control DPWH Philippines":
                # Clean and extract key terms from project description
                cleaned_query = self._clean_search_query(query)
                if cleaned_query:
                    search_terms.append(cleaned_query)
            
            # Add contractor
            if contractor and contractor != "N/A":
                search_terms.append(contractor)
            
            # Add location
            if location:
                search_terms.append(location)
            
            # Combine into search query
            search_query = " ".join(search_terms)
            logger.info(f"Searching web for: {search_query}")
            
            # Perform web search using DuckDuckGo/Bing via aiohttp
            articles = await self._web_search(search_query, n_results)
            
            return articles
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    def _clean_search_query(self, query: str) -> str:
        """Clean and extract meaningful terms from project description"""
        # Remove common filler words
        stop_words = {'construction', 'of', 'the', 'a', 'an', 'in', 'at', 'to', 'for', 'and', 'or'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Keep meaningful words (longer than 3 chars, not stop words)
        meaningful = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Return first 5-6 meaningful words
        return " ".join(meaningful[:6])
    
    async def _web_search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        """Perform web search using DuckDuckGo HTML scraping"""
        articles = []
        
        try:
            # Use DuckDuckGo HTML search (no API key needed)
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            # Create SSL context that doesn't verify certificates
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    search_url,
                    data=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        articles = self._parse_duckduckgo_results(html, max_results)
            
            logger.info(f"Found {len(articles)} articles from web search")
            
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            # Fallback to RSS feeds
            try:
                articles = await self._fetch_live_news(query, max_results)
            except Exception as fallback_error:
                logger.error(f"Fallback RSS search also failed: {fallback_error}")
        
        return articles
    
    def _parse_duckduckgo_results(self, html: str, max_results: int) -> list[NewsArticle]:
        """Parse DuckDuckGo HTML results"""
        articles = []
        
        try:
            # Parse result blocks - DuckDuckGo HTML structure
            # Match title and URL
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>'
            # Match snippet text (may contain HTML tags)
            snippet_pattern = r'<a class="result__snippet"[^>]*>(.*?)</a>'
            
            urls_titles = re.findall(result_pattern, html)
            snippets = re.findall(snippet_pattern, html, re.DOTALL)
            
            # Clean snippets from HTML tags
            clean_snippets = []
            for snippet in snippets:
                # Remove HTML tags
                clean = re.sub(r'<[^>]+>', '', snippet)
                # Remove extra whitespace
                clean = ' '.join(clean.split())
                clean_snippets.append(clean)
            
            for i, (url, title) in enumerate(urls_titles[:max_results]):
                snippet = clean_snippets[i] if i < len(clean_snippets) else "Read more about this flood control project."
                
                # Filter for relevant Philippine news sources
                if any(domain in url.lower() for domain in [
                    'rappler', 'inquirer', 'philstar', 'gma', 'abs-cbn', 
                    'manila', 'philippine', 'dpwh', 'gov.ph', 'news', 'dw.com', 'asia'
                ]):
                    article = NewsArticle(
                        title=self._decode_html(title),
                        snippet=self._decode_html(snippet)[:200] if snippet else "Click to read more about this flood control project.",
                        url=url,
                        source=self._extract_source(url),
                        published_date=datetime.now().isoformat(),
                        relevance_score=1.0 - (i * 0.15)
                    )
                    articles.append(article)
                    
                    if len(articles) >= max_results:
                        break
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return articles
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        try:
            domain = url.split('/')[2].replace('www.', '')
            return domain.split('.')[0].title()
        except:
            return "Web"
    
    def _decode_html(self, text: str) -> str:
        """Decode HTML entities"""
        import html
        return html.unescape(text)

    async def _fetch_live_news(
        self, query: str, max_articles: int = 5
    ) -> list[NewsArticle]:
        """Fetch live news from RSS feeds"""
        articles = []

        try:
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)

                    for entry in feed.entries[:max_articles]:
                        # Simple keyword matching
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")

                        if (
                            "flood" in title.lower()
                            or "flood" in summary.lower()
                            or "DPWH" in title
                            or "infrastructure" in summary.lower()
                        ):
                            article = NewsArticle(
                                title=title,
                                snippet=summary[:200],
                                url=entry.get("link", ""),
                                source=feed.feed.get("title", "Unknown"),
                                published_date=entry.get(
                                    "published", str(datetime.now())
                                ),
                                relevance_score=0.5,
                            )
                            articles.append(article)

                            if len(articles) >= max_articles:
                                break
                except Exception as e:
                    logger.warning(f"Error parsing feed {feed_url}: {e}")
                    continue

                if len(articles) >= max_articles:
                    break

        except Exception as e:
            logger.error(f"Error fetching live news: {e}")

        return articles

    def add_news_to_vector_db(self, articles: list[NewsArticle]):
        """Add news articles to vector database"""
        try:
            collection = self.vector_service.get_or_create_news_collection()

            documents = []
            metadatas = []
            ids = []

            for article in articles:
                # Create document text
                doc_text = f"{article.title} {article.snippet}"

                # Create metadata
                metadata = {
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published_date": article.published_date,
                }

                # Create unique ID
                article_id = hashlib.md5(
                    article.url.encode()
                ).hexdigest()

                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(article_id)

            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
                logger.info(f"Added {len(documents)} news articles to vector DB")

        except Exception as e:
            logger.error(f"Error adding news to vector DB: {e}")