#!/usr/bin/env python3
"""
Qdrant setup and configuration script.

This script sets up Qdrant vector database for RAG functionality,
creates collections, and configures indexing.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CollectionInfo
from qdrant_client.http.exceptions import ResponseHandlingException

from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantSetup:
    """Qdrant setup and configuration service."""
    
    def __init__(self):
        """Initialize Qdrant setup."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        )
        
        self.collections_config = {
            "documents": {
                "vector_size": 1536,  # OpenAI text-embedding-ada-002 size
                "distance": Distance.COSINE,
                "description": "Legislative documents and general documents collection"
            },
            "legislative_docs": {
                "vector_size": 1536,
                "distance": Distance.COSINE,
                "description": "Specific collection for legislative documents"
            },
            "chat_context": {
                "vector_size": 1536,
                "distance": Distance.COSINE,
                "description": "Chat context and conversation history vectors"
            }
        }
    
    async def setup_all(self) -> Dict[str, bool]:
        """Setup all Qdrant collections and configurations.
        
        Returns:
            Dict[str, bool]: Setup results for each collection
        """
        logger.info("🚀 Starting Qdrant setup")
        
        results = {}
        
        try:
            # Check Qdrant connection
            logger.info("🔍 Checking Qdrant connection...")
            await self.check_connection()
            
            # Create collections
            logger.info("📦 Creating collections...")
            for collection_name, config in self.collections_config.items():
                results[collection_name] = await self.create_collection(
                    collection_name, config
                )
            
            # Verify setup
            logger.info("✅ Verifying setup...")
            await self.verify_setup()
            
            logger.info("🎉 Qdrant setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Qdrant setup failed: {e}")
            raise
        
        return results
    
    async def check_connection(self) -> bool:
        """Check connection to Qdrant.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Get cluster info to test connection
            info = self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant - {len(info.collections)} existing collections")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise
    
    async def create_collection(self, collection_name: str, config: Dict[str, Any]) -> bool:
        """Create a Qdrant collection.
        
        Args:
            collection_name: Name of the collection
            config: Collection configuration
            
        Returns:
            bool: True if created successfully
        """
        try:
            # Check if collection already exists
            try:
                existing = self.client.get_collection(collection_name)
                logger.info(f"📦 Collection '{collection_name}' already exists")
                return True
            except ResponseHandlingException:
                # Collection doesn't exist, create it
                pass
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["vector_size"],
                    distance=config["distance"]
                )
            )
            
            logger.info(f"✅ Created collection '{collection_name}' - {config['description']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{collection_name}': {e}")
            return False
    
    async def verify_setup(self) -> None:
        """Verify Qdrant setup by checking collections."""
        try:
            collections = self.client.get_collections()
            
            logger.info("📊 Collection Status:")
            for collection in collections.collections:
                info = self.client.get_collection(collection.name)
                logger.info(f"  - {collection.name}: {info.vectors_count} vectors, {info.status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to verify setup: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection (use with caution).
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"🗑️ Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete collection '{collection_name}': {e}")
            return False
    
    async def recreate_collection(self, collection_name: str) -> bool:
        """Recreate a collection (delete and create).
        
        Args:
            collection_name: Name of collection to recreate
            
        Returns:
            bool: True if recreated successfully
        """
        if collection_name not in self.collections_config:
            logger.error(f"❌ Unknown collection: {collection_name}")
            return False
        
        logger.info(f"🔄 Recreating collection '{collection_name}'...")
        
        # Delete if exists
        try:
            await self.delete_collection(collection_name)
        except:
            pass  # Collection might not exist
        
        # Create new
        return await self.create_collection(
            collection_name, 
            self.collections_config[collection_name]
        )
    
    async def add_sample_data(self) -> None:
        """Add sample data for testing."""
        logger.info("📝 Adding sample data...")
        
        try:
            # Sample document vectors (random for testing)
            import random
            
            sample_points = []
            for i in range(10):
                point = {
                    "id": i,
                    "vector": [random.random() for _ in range(1536)],
                    "payload": {
                        "title": f"Sample Document {i}",
                        "content": f"This is sample content for document {i}",
                        "category": "sample",
                        "user_id": "test_user",
                        "created_at": "2025-01-29T10:00:00Z"
                    }
                }
                sample_points.append(point)
            
            # Add to documents collection
            self.client.upsert(
                collection_name="documents",
                points=sample_points
            )
            
            logger.info("✅ Added 10 sample documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to add sample data: {e}")
    
    async def search_test(self) -> None:
        """Test search functionality."""
        logger.info("🔍 Testing search functionality...")
        
        try:
            import random
            
            # Random search vector
            search_vector = [random.random() for _ in range(1536)]
            
            # Search in documents collection
            results = self.client.search(
                collection_name="documents",
                query_vector=search_vector,
                query_filter={
                    "must": [
                        {"key": "category", "match": {"value": "sample"}}
                    ]
                },
                limit=5
            )
            
            logger.info(f"✅ Search test successful - found {len(results)} results")
            for result in results:
                logger.info(f"  - ID: {result.id}, Score: {result.score:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Search test failed: {e}")


async def main():
    """Main setup function."""
    setup = QdrantSetup()
    
    print("🔥 Qdrant Setup Tool")
    print("This will configure Qdrant for the Ali API RAG system.")
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    
    try:
        # Setup collections
        results = await setup.setup_all()
        
        # Ask if user wants to add sample data
        add_sample = input("\nAdd sample data for testing? (yes/no): ")
        if add_sample.lower() == 'yes':
            await setup.add_sample_data()
            await setup.search_test()
        
        print(f"\n✅ Setup completed successfully!")
        print("Collections created:")
        for collection, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {collection}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")


async def recreate_collection(collection_name: str):
    """Recreate specific collection."""
    setup = QdrantSetup()
    
    print(f"🔄 Recreating collection: {collection_name}")
    confirm = input(f"This will DELETE all data in '{collection_name}'. Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        success = await setup.recreate_collection(collection_name)
        if success:
            print(f"✅ Collection '{collection_name}' recreated successfully")
        else:
            print(f"❌ Failed to recreate collection '{collection_name}'")
    else:
        print("Operation cancelled")


if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description='Qdrant Setup Tool')
    parser.add_argument('--recreate', help='Recreate specific collection')
    args = parser.parse_args()
    
    if args.recreate:
        asyncio.run(recreate_collection(args.recreate))
    else:
        asyncio.run(main())