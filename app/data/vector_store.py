"""
Vector database interface for storing and retrieving document embeddings.
This module handles the interaction with the vector database.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import uuid

import chromadb
from chromadb.config import Settings

from app.config import VECTOR_DB_TYPE, VECTOR_DB_PATH
from app.rag.embedding import embedding_manager
from app.utils import time_operation, system_logger

class VectorStore:
    """Interface to the vector database for document storage and retrieval."""
    
    def __init__(self, db_path: str = str(VECTOR_DB_PATH)):
        """
        Initialize the vector store with connection to the database.
        
        Args:
            db_path: Path to the vector database
        """
        system_logger.info(f"Initializing VectorStore at {db_path}")
        
        self.db_path = db_path
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            system_logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            system_logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
            
        # Create collections if they don't exist
        self._init_collections()
    
    def _init_collections(self):
        """Initialize the collections in the vector database."""
        # Collection for research papers and scientific content
        try:
            self.papers_collection = self.client.get_or_create_collection(
                name="papers",
                metadata={"description": "Scientific papers and research content"}
            )
            
            # Collection for templates and example scripts
            self.templates_collection = self.client.get_or_create_collection(
                name="templates",
                metadata={"description": "Script templates and examples"}
            )
            
            # Collection for threat vectors and scenarios
            self.threats_collection = self.client.get_or_create_collection(
                name="threats",
                metadata={"description": "Threat vectors and security scenarios"}
            )
            
            system_logger.info("Vector store collections initialized successfully")
        except Exception as e:
            system_logger.error(f"Failed to initialize collections: {e}")
            raise
    
    @time_operation
    def add_document(self, 
                     collection_name: str,
                     document: Dict[str, Any],
                     document_id: Optional[str] = None) -> str:
        """
        Add a document to the specified collection.
        
        Args:
            collection_name: Name of the collection to add to
            document: Document data to add
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            The document ID
        """
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        # Get the appropriate collection
        collection = self._get_collection(collection_name)
        
        # Create document embedding
        embedding = embedding_manager.create_document_embedding(document)
        
        # Prepare metadata
        metadata = {
            "source": document.get("source", "unknown"),
            "type": document.get("type", "document"),
            "date_added": document.get("date_added", ""),
        }
        
        # Add additional metadata if available
        for field in ["author", "category", "tags", "title"]:
            if field in document:
                metadata[field] = document[field]
        
        # Add to collection
        try:
            collection.add(
                ids=[document_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata],
                documents=[json.dumps(document)]
            )
            system_logger.info(f"Added document to collection '{collection_name}' with ID: {document_id}")
            return document_id
        except Exception as e:
            system_logger.error(f"Failed to add document to collection '{collection_name}': {e}")
            raise
    
    @time_operation
    def search(self, 
              collection_name: str,
              query: str,
              filter_metadata: Optional[Dict[str, Any]] = None,
              limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query in the specified collection.
        
        Args:
            collection_name: Name of the collection to search
            query: Query text
            filter_metadata: Optional metadata filters
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with similarity scores
        """
        # Get the appropriate collection
        collection = self._get_collection(collection_name)
        
        # Create query embedding
        query_embedding = embedding_manager.embed_query(query)
        
        # Search collection
        try:
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                where=filter_metadata,
                n_results=limit
            )
            
            # Process results
            documents = []
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                
                # Parse the document JSON
                try:
                    doc_content = json.loads(results["documents"][0][i])
                except json.JSONDecodeError:
                    doc_content = {"content": results["documents"][0][i]}
                
                # Get metadata
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                # Calculate score if available
                score = results.get("distances", [[]])[0][i] if "distances" in results else None
                if score is not None:
                    # Convert distance to similarity score (1 - distance)
                    # In ChromaDB, smaller distance = better match
                    similarity = 1.0 - min(score, 1.0)  # Cap at 1.0
                else:
                    similarity = None
                
                documents.append({
                    "id": doc_id,
                    "content": doc_content,
                    "metadata": metadata,
                    "similarity": similarity
                })
            
            system_logger.info(f"Found {len(documents)} results in collection '{collection_name}' for query: {query[:50]}...")
            return documents
        except Exception as e:
            system_logger.error(f"Search error in collection '{collection_name}': {e}")
            return []
    
    def search_all(self, 
                  query: str, 
                  limit_per_collection: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all collections and return combined results.
        
        Args:
            query: Query text
            limit_per_collection: Maximum results per collection
            
        Returns:
            Dictionary of collection names to search results
        """
        results = {}
        for collection_name in ["papers", "templates", "threats"]:
            collection_results = self.search(
                collection_name=collection_name,
                query=query,
                limit=limit_per_collection
            )
            results[collection_name] = collection_results
        
        return results
    
    def _get_collection(self, collection_name: str):
        """Get a collection by name."""
        if collection_name == "papers":
            return self.papers_collection
        elif collection_name == "templates":
            return self.templates_collection
        elif collection_name == "threats":
            return self.threats_collection
        else:
            raise ValueError(f"Unknown collection: {collection_name}")
    
    @time_operation
    def add_batch_documents(self, 
                           collection_name: str,
                           documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple documents to a collection in a single batch operation.
        
        Args:
            collection_name: Name of the collection
            documents: List of document dictionaries
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
            
        collection = self._get_collection(collection_name)
        
        ids = []
        embeddings = []
        metadatas = []
        docs_json = []
        
        # Process each document
        for doc in documents:
            doc_id = doc.get("id", str(uuid.uuid4()))
            ids.append(doc_id)
            
            # Create embedding
            embedding = embedding_manager.create_document_embedding(doc)
            embeddings.append(embedding.tolist())
            
            # Prepare metadata
            metadata = {
                "source": doc.get("source", "unknown"),
                "type": doc.get("type", "document"),
                "date_added": doc.get("date_added", ""),
            }
            
            # Add additional metadata if available
            for field in ["author", "category", "tags", "title"]:
                if field in doc:
                    metadata[field] = doc[field]
                    
            metadatas.append(metadata)
            docs_json.append(json.dumps(doc))
        
        # Add batch to collection
        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=docs_json
            )
            system_logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return ids
        except Exception as e:
            system_logger.error(f"Failed to batch add documents to collection '{collection_name}': {e}")
            raise
    
    def clear_collection(self, collection_name: str) -> None:
        """Clear all documents from a collection."""
        collection = self._get_collection(collection_name)
        try:
            collection.delete(where={})
            system_logger.info(f"Cleared collection '{collection_name}'")
        except Exception as e:
            system_logger.error(f"Failed to clear collection '{collection_name}': {e}")
            raise
    
    def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID from a collection.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to retrieve
            
        Returns:
            Document data or None if not found
        """
        collection = self._get_collection(collection_name)
        
        try:
            result = collection.get(ids=[document_id])
            
            if not result["ids"]:
                return None
                
            # Parse the document JSON
            try:
                doc_content = json.loads(result["documents"][0])
            except json.JSONDecodeError:
                doc_content = {"content": result["documents"][0]}
            
            # Get metadata
            metadata = result["metadatas"][0] if result["metadatas"] else {}
            
            return {
                "id": document_id,
                "content": doc_content,
                "metadata": metadata
            }
        except Exception as e:
            system_logger.error(f"Failed to get document by ID from collection '{collection_name}': {e}")
            return None

# Create a singleton instance
vector_store = VectorStore()