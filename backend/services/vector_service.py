import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for ChromaDB vector operations"""

    def __init__(self):
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            )
        )
        self.projects_collection = None
        self.news_collection = None

    def get_or_create_projects_collection(self):
        """Get or create projects collection"""
        try:
            self.projects_collection = self.client.get_or_create_collection(
                name="projects_collection",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"Projects collection loaded: {self.projects_collection.count()} documents"
            )
            return self.projects_collection
        except Exception as e:
            logger.error(f"Error getting projects collection: {e}")
            raise

    def get_or_create_news_collection(self):
        """Get or create news collection"""
        try:
            self.news_collection = self.client.get_or_create_collection(
                name="news_collection",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"News collection loaded: {self.news_collection.count()} documents"
            )
            return self.news_collection
        except Exception as e:
            logger.error(f"Error getting news collection: {e}")
            raise

    def search_projects(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[dict] = None,
    ) -> dict:
        """Semantic search in projects collection"""
        if self.projects_collection is None:
            self.get_or_create_projects_collection()

        try:
            where_filter = self._build_where_filter(filters) if filters else None

            results = self.projects_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

            return results
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return {"ids": [[]], "metadatas": [[]], "documents": [[]]}

    def search_news(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[dict] = None,
    ) -> dict:
        """Semantic search in news collection"""
        if self.news_collection is None:
            self.get_or_create_news_collection()

        try:
            where_filter = self._build_where_filter(filters) if filters else None

            results = self.news_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

            return results
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return {"ids": [[]], "metadatas": [[]], "documents": [[]]}

    def _build_where_filter(self, filters: dict) -> dict:
        """Build ChromaDB where filter from dict"""
        where = {}

        # Handle different filter types
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    where[key] = {"$in": value}
                elif isinstance(value, (int, float)):
                    where[key] = value
                elif isinstance(value, str):
                    where[key] = value

        return where if where else None