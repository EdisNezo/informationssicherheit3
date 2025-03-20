"""
Document loader for parsing and processing documents to be stored in the vector database.
This module handles loading various document types and preparing them for embedding.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

from app.config import DOCS_DIR
from app.data.vector_store import vector_store
from app.utils import system_logger, time_operation

class DocumentLoader:
    """Loader for parsing and processing documents."""
    
    def __init__(self, docs_dir: Path = DOCS_DIR):
        """
        Initialize the document loader.
        
        Args:
            docs_dir: Base directory for documents
        """
        self.docs_dir = docs_dir
        system_logger.info(f"Initialized DocumentLoader with docs_dir: {docs_dir}")
    
    @time_operation
    def load_document(self, 
                     filepath: Union[str, Path], 
                     collection: str,
                     metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Load a single document and add it to the vector store.
        
        Args:
            filepath: Path to the document
            collection: Collection name to add to
            metadata: Optional additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        filepath = Path(filepath)
        if not filepath.exists():
            system_logger.error(f"Document not found: {filepath}")
            return None
        
        try:
            # Process document based on file type
            document = self._process_file(filepath, metadata)
            
            if document:
                # Add to vector store
                document_id = vector_store.add_document(collection, document)
                system_logger.info(f"Added document to collection '{collection}': {filepath.name} (ID: {document_id})")
                return document_id
            else:
                system_logger.warning(f"Failed to process document: {filepath}")
                return None
        except Exception as e:
            system_logger.error(f"Error loading document {filepath}: {e}")
            return None
    
    @time_operation
    def load_directory(self, 
                      directory: Union[str, Path], 
                      collection: str,
                      recursive: bool = True,
                      file_extensions: Optional[List[str]] = None) -> List[str]:
        """
        Load all documents in a directory and add them to the vector store.
        
        Args:
            directory: Directory containing documents
            collection: Collection name to add to
            recursive: Whether to search subdirectories
            file_extensions: List of file extensions to include
            
        Returns:
            List of document IDs
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            system_logger.error(f"Directory not found: {directory}")
            return []
        
        # Default file extensions to process
        if file_extensions is None:
            file_extensions = ['.txt', '.md', '.pdf', '.json']
        
        # Find all matching files
        all_files = []
        if recursive:
            for ext in file_extensions:
                all_files.extend(list(directory.glob(f"**/*{ext}")))
        else:
            for ext in file_extensions:
                all_files.extend(list(directory.glob(f"*{ext}")))
        
        system_logger.info(f"Found {len(all_files)} files in directory {directory}")
        
        # Process each file and collect documents
        documents = []
        for filepath in all_files:
            try:
                document = self._process_file(filepath)
                if document:
                    documents.append(document)
            except Exception as e:
                system_logger.error(f"Error processing file {filepath}: {e}")
        
        # Add batch documents to vector store
        if documents:
            try:
                document_ids = vector_store.add_batch_documents(collection, documents)
                system_logger.info(f"Added {len(document_ids)} documents to collection '{collection}'")
                return document_ids
            except Exception as e:
                system_logger.error(f"Error adding batch documents to collection '{collection}': {e}")
                return []
        else:
            system_logger.warning(f"No valid documents found in {directory}")
            return []
    
    def _process_file(self, filepath: Path, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Process a file and convert it to a document dictionary.
        
        Args:
            filepath: Path to the file
            metadata: Optional additional metadata
            
        Returns:
            Document dictionary or None if processing failed
        """
        file_extension = filepath.suffix.lower()
        
        # Base metadata
        doc_metadata = {
            "source": str(filepath),
            "filename": filepath.name,
            "date_added": datetime.now().isoformat(),
        }
        
        # Add additional metadata if provided
        if metadata:
            doc_metadata.update(metadata)
        
        # Process based on file type
        if file_extension in ['.txt', '.md']:
            return self._process_text_file(filepath, doc_metadata)
        elif file_extension == '.json':
            return self._process_json_file(filepath, doc_metadata)
        elif file_extension == '.pdf':
            return self._process_pdf_file(filepath, doc_metadata)
        else:
            system_logger.warning(f"Unsupported file type: {file_extension}")
            return None
    
    def _process_text_file(self, filepath: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a plain text or markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first line if possible
            lines = content.split('\n')
            title = lines[0].strip('# ') if lines and lines[0].startswith('#') else filepath.stem
            
            return {
                "title": title,
                "content": content,
                "type": "text",
                "metadata": metadata
            }
        except Exception as e:
            system_logger.error(f"Error reading text file {filepath}: {e}")
            return None
    
    def _process_json_file(self, filepath: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # If JSON is already in document format, just add metadata
            if isinstance(data, dict) and "content" in data:
                data["metadata"] = metadata
                return data
            
            # Otherwise, wrap the JSON in a document
            return {
                "title": data.get("title", filepath.stem),
                "content": json.dumps(data),
                "type": "json",
                "metadata": metadata
            }
        except Exception as e:
            system_logger.error(f"Error reading JSON file {filepath}: {e}")
            return None
    
    def _process_pdf_file(self, filepath: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a PDF file."""
        try:
            # In a real implementation, we would use a PDF parser like PyPDF2 or pdfplumber
            # For this example, we'll simulate PDF processing
            system_logger.info(f"Processing PDF file: {filepath}")
            
            # Simulated content extraction
            content = f"Simulated content from PDF file: {filepath.name}"
            
            return {
                "title": filepath.stem,
                "content": content,
                "type": "pdf",
                "metadata": metadata
            }
        except Exception as e:
            system_logger.error(f"Error reading PDF file {filepath}: {e}")
            return None
    
    def load_threatmap(self, filepath: Union[str, Path]) -> List[str]:
        """
        Load a threat map JSON file containing structured threat vectors.
        
        Args:
            filepath: Path to the threat map JSON file
            
        Returns:
            List of document IDs
        """
        filepath = Path(filepath)
        if not filepath.exists():
            system_logger.error(f"Threat map file not found: {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                threat_data = json.load(f)
                
            if not isinstance(threat_data, list):
                system_logger.error(f"Invalid threat map format in {filepath}")
                return []
                
            documents = []
            for threat in threat_data:
                if not isinstance(threat, dict):
                    continue
                    
                # Create a structured document for the threat
                doc = {
                    "title": threat.get("name", "Unnamed Threat"),
                    "threat_type": threat.get("type", "unknown"),
                    "description": threat.get("description", ""),
                    "impact": threat.get("impact", ""),
                    "mitigations": threat.get("mitigations", []),
                    "examples": threat.get("examples", []),
                    "type": "threat_vector",
                    "metadata": {
                        "source": str(filepath),
                        "category": threat.get("category", "general"),
                        "severity": threat.get("severity", "medium"),
                        "date_added": datetime.now().isoformat()
                    }
                }
                
                documents.append(doc)
                
            # Add batch documents to vector store
            if documents:
                document_ids = vector_store.add_batch_documents("threats", documents)
                system_logger.info(f"Added {len(document_ids)} threat vectors from {filepath}")
                return document_ids
            else:
                system_logger.warning(f"No valid threat vectors found in {filepath}")
                return []
                
        except Exception as e:
            system_logger.error(f"Error loading threat map {filepath}: {e}")
            return []
    
    def chunk_document(self, document: Dict[str, Any], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split a large document into smaller chunks for more effective retrieval.
        
        Args:
            document: Document dictionary
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of document chunks
        """
        content = document.get("content", "")
        if not content or len(content) <= chunk_size:
            return [document]
            
        chunks = []
        
        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save the current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunk_doc = document.copy()
                chunk_doc["content"] = current_chunk
                chunk_doc["chunk_id"] = len(chunks)
                chunks.append(chunk_doc)
                
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the final chunk
        if current_chunk:
            chunk_doc = document.copy()
            chunk_doc["content"] = current_chunk
            chunk_doc["chunk_id"] = len(chunks)
            chunks.append(chunk_doc)
            
        return chunks

# Create a singleton instance
document_loader = DocumentLoader()