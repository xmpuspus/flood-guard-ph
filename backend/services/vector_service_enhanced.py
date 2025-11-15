"""Enhanced Vector Service with actual semantic search

Enhancement #2: Activate Vector Database Semantic Search
"""
import logging
from typing import Optional, List, Dict
import hashlib

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings

from backend.config import settings
from backend.models.errors import ErrorCode, FloodGuardException

logger = logging.getLogger(__name__)


class EnhancedVectorService:
    """
    Enhanced vector service with active semantic search

    Enhancement #2: Activate Vector DB
    """

    def __init__(self, openai_key: Optional[str] = None):
        try:
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise FloodGuardException(
                ErrorCode.VECTOR_DB_ERROR,
                f"Vector database initialization failed: {str(e)}"
            )

        # Initialize embeddings (use user key if provided)
        self.embeddings = None
        if openai_key or settings.openai_api_key != "dummy":
            try:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=openai_key or settings.openai_api_key,
                    model="text-embedding-3-small"
                )
                logger.info("✓ OpenAI embeddings initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize embeddings: {e}")

        self.projects_collection = None
        self.news_collection = None

        # Initialize collections
        self.get_or_create_projects_collection()
        self.get_or_create_news_collection()

    def get_or_create_projects_collection(self):
        """Get or create projects collection"""
        try:
            self.projects_collection = self.client.get_or_create_collection(
                name="projects_collection",
                metadata={"hnsw:space": "cosine"},
            )
            count = self.projects_collection.count()
            logger.info(f"✓ Projects collection: {count} documents")
            return self.projects_collection
        except Exception as e:
            logger.error(f"Error with projects collection: {e}")
            raise FloodGuardException(
                ErrorCode.VECTOR_DB_ERROR,
                f"Failed to access projects collection: {str(e)}"
            )

    def get_or_create_news_collection(self):
        """Get or create news collection"""
        try:
            self.news_collection = self.client.get_or_create_collection(
                name="news_collection",
                metadata={"hnsw:space": "cosine"},
            )
            count = self.news_collection.count()
            logger.info(f"✓ News collection: {count} documents")
            return self.news_collection
        except Exception as e:
            logger.error(f"Error with news collection: {e}")
            raise FloodGuardException(
                ErrorCode.VECTOR_DB_ERROR,
                f"Failed to access news collection: {str(e)}"
            )

    def add_projects(self, projects_df, batch_size: int = 100):
        """
        Add/update projects in vector database

        Args:
            projects_df: DataFrame with project data
            batch_size: Number of projects to process per batch
        """
        if self.embeddings is None:
            logger.warning("No embeddings available, skipping vector indexing")
            return

        try:
            total = len(projects_df)
            logger.info(f"Adding {total} projects to vector database...")

            # Process in batches
            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch_df = projects_df.iloc[start_idx:end_idx]

                # Prepare batch data
                ids = []
                documents = []
                metadatas = []

                for _, row in batch_df.iterrows():
                    # Create unique ID
                    project_id = str(row.get('ProjectComponentID', ''))
                    if not project_id:
                        continue

                    # Create searchable document text
                    doc_parts = []

                    if pd.notna(row.get('ProjectDescription')):
                        doc_parts.append(str(row['ProjectDescription']))

                    if pd.notna(row.get('Contractor')):
                        doc_parts.append(f"Contractor: {row['Contractor']}")

                    if pd.notna(row.get('Municipality')):
                        doc_parts.append(f"Location: {row['Municipality']}")

                    if pd.notna(row.get('Province')):
                        doc_parts.append(f"Province: {row['Province']}")

                    if pd.notna(row.get('TypeofWork')):
                        doc_parts.append(f"Type: {row['TypeofWork']}")

                    if pd.notna(row.get('InfraYear')):
                        doc_parts.append(f"Year: {int(row['InfraYear'])}")

                    document = " | ".join(doc_parts)

                    # Create metadata
                    metadata = {
                        'project_id': project_id,
                        'contractor': str(row.get('Contractor', ''))[:100],
                        'province': str(row.get('Province', ''))[:100],
                        'municipality': str(row.get('Municipality', ''))[:100],
                        'region': str(row.get('Region', ''))[:100],
                        'year': int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else 0,
                        'cost': float(row.get('ContractCost', 0)) if pd.notna(row.get('ContractCost')) else 0,
                    }

                    ids.append(project_id)
                    documents.append(document)
                    metadatas.append(metadata)

                # Generate embeddings for batch
                try:
                    embeddings_list = self.embeddings.embed_documents(documents)

                    # Add to collection
                    self.projects_collection.add(
                        ids=ids,
                        documents=documents,
                        embeddings=embeddings_list,
                        metadatas=metadatas
                    )

                    logger.info(f"Added batch {start_idx}-{end_idx} ({len(ids)} projects)")

                except Exception as e:
                    logger.error(f"Error embedding batch {start_idx}-{end_idx}: {e}")
                    continue

            logger.info(f"✓ Successfully indexed {total} projects")

        except Exception as e:
            logger.error(f"Error adding projects to vector DB: {e}")
            raise FloodGuardException(
                ErrorCode.VECTOR_DB_ERROR,
                f"Failed to index projects: {str(e)}"
            )

    def semantic_search_projects(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform semantic search on projects

        Enhancement #2: Active semantic search
        """
        if self.projects_collection is None:
            raise FloodGuardException(
                ErrorCode.VECTOR_DB_ERROR,
                "Projects collection not initialized"
            )

        try:
            # Build where filter
            where_filter = None
            if filters:
                where_filter = {}
                if 'year' in filters and filters['year']:
                    where_filter['year'] = {"$in": filters['year']}
                if 'province' in filters and filters['province']:
                    where_filter['province'] = filters['province']
                if 'contractor' in filters and filters['contractor']:
                    where_filter['contractor'] = {"$contains": filters['contractor']}

            # Perform search
            results = self.projects_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )

            # Format results
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i, project_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    document = results['documents'][0][i] if results.get('documents') else ""
                    distance = results['distances'][0][i] if results.get('distances') else 1.0

                    formatted_results.append({
                        'project_id': project_id,
                        'metadata': metadata,
                        'snippet': document[:200],
                        'similarity_score': 1.0 - distance,  # Convert distance to similarity
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def search_news(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Semantic search in news collection"""
        if self.news_collection is None or self.news_collection.count() == 0:
            logger.warning("News collection empty")
            return []

        try:
            where_filter = self._build_where_filter(filters) if filters else None

            results = self.news_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )

            # Format results
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i, news_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    document = results['documents'][0][i] if results.get('documents') else ""
                    distance = results['distances'][0][i] if results.get('distances') else 1.0

                    formatted_results.append({
                        'id': news_id,
                        'title': metadata.get('title', ''),
                        'url': metadata.get('url', ''),
                        'source': metadata.get('source', ''),
                        'snippet': document[:300],
                        'relevance_score': 1.0 - distance,
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"News search error: {e}")
            return []

    def _build_where_filter(self, filters: Dict) -> Optional[Dict]:
        """Build ChromaDB where filter"""
        if not filters:
            return None

        where = {}
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    where[key] = {"$in": value}
                elif isinstance(value, (int, float, str)):
                    where[key] = value

        return where if where else None

    def get_collection_stats(self) -> Dict:
        """Get statistics about vector collections"""
        return {
            'projects': {
                'count': self.projects_collection.count() if self.projects_collection else 0,
                'name': 'projects_collection'
            },
            'news': {
                'count': self.news_collection.count() if self.news_collection else 0,
                'name': 'news_collection'
            },
            'embeddings_enabled': self.embeddings is not None
        }


# Import pandas here to avoid circular imports
import pandas as pd
