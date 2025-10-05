#!/usr/bin/env python3
"""
Embed projects into ChromaDB for semantic search
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import OpenAIEmbeddings

from backend.config import settings
from backend.services.project_service import ProjectService
from backend.services.vector_service import VectorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Embed all projects into ChromaDB"""
    try:
        logger.info("Starting project embedding...")

        # Initialize services
        logger.info("Loading project data...")
        project_service = ProjectService()

        if project_service.df is None or len(project_service.df) == 0:
            logger.error("No projects loaded!")
            sys.exit(1)

        logger.info(f"Loaded {len(project_service.df)} projects")

        # Initialize vector service
        logger.info("Initializing vector service...")
        vector_service = VectorService()
        collection = vector_service.get_or_create_projects_collection()

        # Check if already embedded
        existing_count = collection.count()
        if existing_count > 0:
            logger.warning(
                f"Collection already has {existing_count} documents"
            )
            response = input("Delete and re-embed? (y/N): ")
            if response.lower() == "y":
                logger.info("Deleting existing collection...")
                vector_service.client.delete_collection("projects_collection")
                collection = vector_service.get_or_create_projects_collection()
            else:
                logger.info("Skipping embedding")
                return

        # Initialize embeddings
        logger.info("Initializing OpenAI embeddings...")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key,
        )

        # Prepare data for embedding
        logger.info("Preparing documents for embedding...")
        documents = []
        metadatas = []
        ids = []

        seen_ids = set()
        for idx, row in project_service.df.iterrows():
            # Create document text
            doc_parts = [
                str(row.get("ProjectDescription", "")),
                str(row.get("Contractor", "")),
                str(row.get("Municipality", "")),
                str(row.get("Province", "")),
                str(row.get("TypeofWork", "")),
                str(row.get("InfraYear", "")),
            ]
            doc_text = " ".join(filter(None, doc_parts))

            # Create metadata
            metadata = {
                "project_id": str(row.get("ProjectID", "")),
                "contractor": str(row.get("Contractor", "")),
                "contract_cost": float(row.get("ContractCost", 0)),
                "abc": float(row.get("ABC", 0)),
                "region": str(row.get("Region", "")),
                "province": str(row.get("Province", "")),
                "municipality": str(row.get("Municipality", "")),
                "infra_year": int(row.get("InfraYear", 0))
                if row.get("InfraYear")
                else 0,
                "type_of_work": str(row.get("TypeofWork", "")),
                "lat": float(row.get("Latitude", 0)),
                "lon": float(row.get("Longitude", 0)),
            }

            # Use ProjectComponentID as unique ID, but handle duplicates
            doc_id = str(row.get("ProjectComponentID", ""))
            
            # If duplicate, append row index to make it unique
            if doc_id in seen_ids:
                doc_id = f"{doc_id}_{idx}"
            
            seen_ids.add(doc_id)

            if doc_text and doc_id:
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(doc_id)

        logger.info(f"Prepared {len(documents)} documents")

        # Embed in batches
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size

        logger.info(f"Embedding in {total_batches} batches...")

        for i in range(0, len(documents), batch_size):
            batch_num = (i // batch_size) + 1
            logger.info(f"Processing batch {batch_num}/{total_batches}...")

            batch_docs = documents[i : i + batch_size]
            batch_metas = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]

            # Generate embeddings
            batch_embeddings = embeddings.embed_documents(batch_docs)

            # Add to collection
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids,
                embeddings=batch_embeddings,
            )

            logger.info(f"✓ Batch {batch_num} complete")

        logger.info(f"\n✓ Successfully embedded {len(documents)} projects!")
        logger.info(f"Collection now has {collection.count()} documents")

        logger.info("\nNext step:")
        logger.info("  Start server: uvicorn backend.main:app --reload")

    except Exception as e:
        logger.error(f"Error embedding projects: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()