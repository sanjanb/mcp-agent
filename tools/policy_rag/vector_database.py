"""
Vector database management for HR Policy RAG Agent.
Handles embedding creation, storage, and similarity search using Chroma.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid
import json
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDatabase:
    """Manages vector database operations for HR document embeddings."""
    
    def __init__(
        self, 
        db_path: str = "./data/vector_db",
        collection_name: str = "hr_policies",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector database.
        
        Args:
            db_path: Path to store the vector database
            collection_name: Name of the collection to store embeddings
            embedding_model: Name of the sentence transformer model
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "HR policy documents and embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        logger.info(f"VectorDatabase initialized with {self.collection.count()} documents")
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Creating embeddings for {len(texts)} texts")
        
        try:
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_tensor=False,
                show_progress_bar=True
            )
            
            # Convert to list format for Chroma
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            logger.info(f"Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add document chunks to the vector database.
        
        Args:
            chunks: List of document chunks with text and metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not chunks:
            logger.warning("No chunks provided to add to database")
            return True
        
        logger.info(f"Adding {len(chunks)} chunks to vector database")
        
        try:
            # Extract texts and create embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.create_embeddings(texts)
            
            # Create unique IDs for each chunk
            ids = [str(uuid.uuid4()) for _ in chunks]
            
            # Prepare metadata (Chroma requires string values)
            metadatas = []
            for chunk in chunks:
                metadata = {
                    'doc_id': str(chunk.get('doc_id', '')),
                    'filename': str(chunk.get('filename', '')),
                    'page_number': str(chunk.get('page_number', 1)),
                    'total_pages': str(chunk.get('total_pages', 1)),
                    'chunk_id': str(chunk.get('chunk_id', 0)),
                    'token_count': str(chunk.get('token_count', 0)),
                    'doc_type': str(chunk.get('doc_type', 'unknown')),
                    'added_at': datetime.now().isoformat()
                }
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to database: {e}")
            return False
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using a text query.
        
        Args:
            query: Text query to search for
            top_k: Number of top results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with text, metadata, and scores
        """
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        try:
            # Create query embedding
            query_embedding = self.create_embeddings([query])[0]
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': float(1 - results['distances'][0][i]),  # Convert distance to similarity
                        'doc_id': results['metadatas'][0][i].get('doc_id', ''),
                        'page_number': int(results['metadatas'][0][i].get('page_number', 1)),
                        'filename': results['metadatas'][0][i].get('filename', '')
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            doc_types = {}
            filenames = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    doc_type = metadata.get('doc_type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    filenames.add(metadata.get('filename', 'unknown'))
            
            stats = {
                'total_chunks': count,
                'unique_documents': len(filenames),
                'doc_types': doc_types,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model_name
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if successful, False otherwise
        """
        logger.warning("Clearing all documents from collection")
        
        try:
            # Get all document IDs
            all_docs = self.collection.get()
            
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
                logger.info(f"Cleared {len(all_docs['ids'])} documents from collection")
            else:
                logger.info("Collection was already empty")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting document: {doc_id}")
        
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"]
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {doc_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Test the vector database
    from document_processor import DocumentProcessor
    
    # Initialize components
    db = VectorDatabase()
    processor = DocumentProcessor(chunk_size=200)
    
    print("\n=== Vector Database Test ===")
    
    # Check current stats
    stats = db.get_collection_stats()
    print(f"Current collection stats: {stats}")
    
    # Process sample documents if available
    hr_docs_path = "../data/hr_documents"
    if Path(hr_docs_path).exists():
        chunks = processor.process_directory(hr_docs_path)
        
        if chunks:
            print(f"\nProcessed {len(chunks)} chunks from documents")
            
            # Add to database
            success = db.add_documents(chunks)
            if success:
                print("Successfully added documents to database")
                
                # Test search
                test_queries = [
                    "vacation time",
                    "sick leave policy",
                    "remote work",
                    "health insurance benefits"
                ]
                
                for query in test_queries:
                    print(f"\n--- Search: '{query}' ---")
                    results = db.search(query, top_k=2)
                    
                    for i, result in enumerate(results, 1):
                        print(f"Result {i} (score: {result['score']:.3f}):")
                        print(f"  Doc: {result['filename']} (page {result['page_number']})")
                        print(f"  Text: {result['text'][:150]}...")
            
            # Final stats
            final_stats = db.get_collection_stats()
            print(f"\nFinal collection stats: {final_stats}")
        else:
            print("No documents found to process")
    else:
        print(f"HR documents directory not found: {hr_docs_path}")
        print("Please create some sample documents to test with")