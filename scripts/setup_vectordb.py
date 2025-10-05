#!/usr/bin/env python3
"""
Initialize ChromaDB collections for FloodWatch PH
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.services.vector_service import VectorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Initialize ChromaDB collections"""
    try:
        logger.info("Initializing ChromaDB...")
        logger.info(f"Persist directory: {settings.chroma_persist_dir}")

        # Create persist directory if it doesn't exist
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize vector service
        vector_service = VectorService()

        # Create collections
        logger.info("Creating projects collection...")
        projects_collection = vector_service.get_or_create_projects_collection()
        logger.info(
            f"✓ Projects collection ready: {projects_collection.count()} documents"
        )

        logger.info("Creating news collection...")
        news_collection = vector_service.get_or_create_news_collection()
        logger.info(
            f"✓ News collection ready: {news_collection.count()} documents"
        )

        logger.info("\n✓ ChromaDB setup complete!")
        logger.info(
            "\nNext steps:"
        )
        logger.info("  1. Run: python scripts/embed_projects.py")
        logger.info("  2. Start server: uvicorn backend.main:app --reload")

    except Exception as e:
        logger.error(f"Error setting up ChromaDB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()