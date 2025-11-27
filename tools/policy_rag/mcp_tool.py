"""
MCP Tool for HR Policy Search.
Implements the policy_search tool that retrieves relevant HR document chunks.
"""

import logging
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import os
import sys

# Add the tools directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from policy_rag.vector_database import VectorDatabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicySearchTool:
    """MCP Tool for searching HR policy documents."""
    
    def __init__(self, db_path: str = "./data/vector_db"):
        """
        Initialize the policy search tool.
        
        Args:
            db_path: Path to the vector database
        """
        self.db_path = db_path
        self.vector_db = None
        logger.info("PolicySearchTool initialized")
    
    def _ensure_db_connection(self) -> bool:
        """
        Ensure vector database connection is established.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.vector_db is None:
            try:
                self.vector_db = VectorDatabase(db_path=self.db_path)
                logger.info("Vector database connection established")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to vector database: {e}")
                return False
        return True
    
    def search_policies(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for relevant HR policy chunks.
        
        This is the main function that implements the MCP tool functionality.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (max 10)
            
        Returns:
            Dictionary with search results in MCP tool format
        """
        logger.info(f"Policy search request: query='{query}', top_k={top_k}")
        
        # Validate inputs
        if not query or not query.strip():
            return {
                "error": "Query cannot be empty",
                "query": query,
                "chunks": []
            }
        
        # Limit top_k to reasonable range
        top_k = max(1, min(top_k, 10))
        
        # Ensure database connection
        if not self._ensure_db_connection():
            return {
                "error": "Failed to connect to vector database",
                "query": query,
                "chunks": []
            }
        
        try:
            # Perform search
            search_results = self.vector_db.search(query, top_k=top_k)
            
            # Format results for MCP tool output
            chunks = []
            for result in search_results:
                chunk = {
                    "doc_id": result.get("doc_id", ""),
                    "text": result.get("text", ""),
                    "score": round(result.get("score", 0.0), 3),
                    "page": int(result.get("page_number", 1)),
                    "filename": result.get("filename", ""),
                    "metadata": {
                        "chunk_id": result.get("metadata", {}).get("chunk_id", ""),
                        "token_count": result.get("metadata", {}).get("token_count", ""),
                        "doc_type": result.get("metadata", {}).get("doc_type", "")
                    }
                }
                chunks.append(chunk)
            
            response = {
                "query": query,
                "chunks": chunks,
                "total_results": len(chunks),
                "search_successful": True
            }
            
            logger.info(f"Policy search completed: {len(chunks)} results found")
            return response
            
        except Exception as e:
            logger.error(f"Policy search failed: {e}")
            return {
                "error": f"Search failed: {str(e)}",
                "query": query,
                "chunks": []
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the policy database.
        
        Returns:
            Dictionary with database statistics
        """
        logger.info("Getting database statistics")
        
        if not self._ensure_db_connection():
            return {"error": "Failed to connect to vector database"}
        
        try:
            stats = self.vector_db.get_collection_stats()
            logger.info("Database stats retrieved successfully")
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": f"Failed to get stats: {str(e)}"}


# MCP Tool Interface Functions
# These functions provide the MCP-compatible interface

def policy_search(query: str, top_k: int = 5) -> str:
    """
    MCP Tool function: Search HR policy documents.
    
    Args:
        query: Search query string
        top_k: Number of top results to return
        
    Returns:
        JSON string with search results
    """
    tool = PolicySearchTool()
    result = tool.search_policies(query, top_k)
    return json.dumps(result, indent=2)


def get_policy_stats() -> str:
    """
    MCP Tool function: Get database statistics.
    
    Returns:
        JSON string with database statistics
    """
    tool = PolicySearchTool()
    result = tool.get_database_stats()
    return json.dumps(result, indent=2)


# Tool Registry for MCP Server
MCP_TOOLS = {
    "policy_search": {
        "function": policy_search,
        "description": "Search HR policy documents using semantic similarity",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for finding relevant policy information"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results to return (1-10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    },
    "get_policy_stats": {
        "function": get_policy_stats,
        "description": "Get statistics about the HR policy database",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


# Example usage and testing
if __name__ == "__main__":
    print("\n=== Policy Search Tool Test ===")
    
    # Initialize tool
    tool = PolicySearchTool()
    
    # Test database stats
    print("\n--- Database Stats ---")
    stats = tool.get_database_stats()
    print(json.dumps(stats, indent=2))
    
    # Test searches
    test_queries = [
        "vacation policy",
        "sick leave",
        "remote work guidelines", 
        "health benefits"
    ]
    
    for query in test_queries:
        print(f"\n--- Search: '{query}' ---")
        result = tool.search_policies(query, top_k=2)
        
        if result.get("chunks"):
            for i, chunk in enumerate(result["chunks"], 1):
                print(f"Result {i} (score: {chunk['score']}):")
                print(f"  File: {chunk['filename']} (page {chunk['page']})")
                print(f"  Text: {chunk['text'][:100]}...")
        else:
            print(f"No results found. Error: {result.get('error', 'Unknown')}")
    
    print("\n--- MCP Tool Interface Test ---")
    # Test MCP-style function calls
    mcp_result = policy_search("vacation time", 3)
    print("MCP Function Result:")
    print(mcp_result)