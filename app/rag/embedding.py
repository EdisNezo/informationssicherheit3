"""
Embedding module for converting text to vector representations.
This module provides functions for creating and managing embeddings for the RAG system.
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL
from app.utils import time_operation, system_logger

class EmbeddingManager:
    """Manager for creating and storing text embeddings."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the embedding manager with a specific model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        system_logger.info(f"Initializing EmbeddingManager with model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            system_logger.info(f"Embedding model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            system_logger.error(f"Failed to load embedding model: {e}")
            raise
    
    @time_operation
    def create_embedding(self, text: str) -> np.ndarray:
        """
        Create an embedding vector for a single text string.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding vector as a numpy array
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    @time_operation
    def create_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Create embedding vectors for a list of text strings.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.model.encode(texts, convert_to_numpy=True)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (between -1 and 1)
        """
        # Normalize the vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        return np.dot(embedding1, embedding2) / (norm1 * norm2)
    
    def create_document_embedding(self, 
                                document: Dict[str, Any], 
                                fields: Optional[List[str]] = None) -> np.ndarray:
        """
        Create an embedding for a document by combining specified fields.
        
        Args:
            document: Document dictionary
            fields: List of field names to include in the embedding
            
        Returns:
            Combined embedding vector
        """
        if fields is None:
            # Default to these fields if available
            fields = ["title", "content", "description"]
        
        # Collect available text from the specified fields
        texts = []
        for field in fields:
            if field in document and document[field]:
                texts.append(str(document[field]))
        
        # Combine all texts with spaces
        combined_text = " ".join(texts)
        
        if not combined_text:
            system_logger.warning(f"No text found in document for embedding: {document.get('id', 'unknown')}")
            # Return zero vector with correct dimension
            return np.zeros(self.dimension)
        
        return self.create_embedding(combined_text)
    
    def embed_query(self, query: str, context: Optional[str] = None) -> np.ndarray:
        """
        Create an embedding for a user query, optionally with context.
        
        Args:
            query: The user's query text
            context: Optional context to include
            
        Returns:
            Query embedding vector
        """
        if context:
            # Combine query with context for better retrieval
            query_text = f"{query} {context}"
        else:
            query_text = query
            
        return self.create_embedding(query_text)

# Create a singleton instance
embedding_manager = EmbeddingManager()