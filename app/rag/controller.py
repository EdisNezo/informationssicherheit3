"""
RAG Controller module that orchestrates the retrieval and generation process.
This module coordinates between the vector database, embedding model, and LLM.
"""

from typing import Dict, List, Any, Optional, Tuple
import json

from app.data.vector_store import vector_store
from app.rag.embedding import embedding_manager
from app.utils import system_logger, time_operation
from app.config import HALLUCINATION_MANAGEMENT

class RAGController:
    """Controller for orchestrating the RAG (Retrieval-Augmented Generation) process."""
    
    def __init__(self):
        """Initialize the RAG controller."""
        system_logger.info("Initializing RAG Controller")
    
    @time_operation
    def retrieve_context(self, 
                        query: str, 
                        session_context: Dict[str, Any],
                        limit_per_collection: int = 3) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query from the vector database.
        
        Args:
            query: User query or strategic question
            session_context: Current session context for better retrieval
            limit_per_collection: Maximum number of results per collection
            
        Returns:
            Dictionary containing retrieved context and documents
        """
        system_logger.info(f"Retrieving context for query: {query[:50]}...")
        
        # Enrich query with session context if available
        enriched_query = query
        
        if session_context:
            # Add facility type and target audience from session context
            facility = session_context.get("facility_type", "")
            audience = session_context.get("target_audience", [])
            
            if facility:
                enriched_query += f" in {facility}"
                
            if audience and isinstance(audience, list) and len(audience) > 0:
                audience_str = ", ".join(audience[:3])  # Limit to first 3 for brevity
                enriched_query += f" for {audience_str}"
                
            # Add focus threats if available
            threats = session_context.get("focus_threats", [])
            if threats and isinstance(threats, list) and len(threats) > 0:
                threats_str = ", ".join(threats[:3])  # Limit to first 3
                enriched_query += f" focusing on {threats_str}"
        
        system_logger.debug(f"Enriched query: {enriched_query}")
        
        # Retrieve from all collections
        results = vector_store.search_all(
            query=enriched_query,
            limit_per_collection=limit_per_collection
        )
        
        # Process and format results
        processed_results = self._process_search_results(results)
        
        # Add metadata about the retrieval
        retrieval_info = {
            "original_query": query,
            "enriched_query": enriched_query,
            "total_documents": sum(len(docs) for docs in results.values()),
            "collection_counts": {coll: len(docs) for coll, docs in results.items()}
        }
        
        return {
            "documents": processed_results,
            "retrieval_info": retrieval_info
        }
    
    def _process_search_results(self, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process and format search results for better prompt construction."""
        processed = {}
        
        for collection, documents in results.items():
            processed_docs = []
            
            for doc in documents:
                # Extract the content
                if "content" in doc:
                    content = doc["content"]
                    
                    # If content is a dictionary, handle it appropriately
                    if isinstance(content, dict):
                        processed_content = {}
                        
                        # For templates, extract title and content
                        if collection == "templates":
                            processed_content = {
                                "title": content.get("title", "Untitled Template"),
                                "description": content.get("description", ""),
                                "content": content.get("content", "")
                            }
                        # For threats, extract key information
                        elif collection == "threats":
                            processed_content = {
                                "title": content.get("title", "Unnamed Threat"),
                                "type": content.get("threat_type", "unknown"),
                                "description": content.get("description", ""),
                                "impact": content.get("impact", ""),
                                "mitigations": content.get("mitigations", [])
                            }
                        # For papers, extract title and content
                        else:
                            processed_content = {
                                "title": content.get("title", "Untitled Document"),
                                "content": content.get("content", "")
                            }
                    else:
                        # If it's a string (or other type), use as is
                        processed_content = content
                        
                    # Create processed document
                    processed_doc = {
                        "id": doc.get("id", ""),
                        "content": processed_content,
                        "similarity": doc.get("similarity", None),
                        "metadata": doc.get("metadata", {})
                    }
                    
                    processed_docs.append(processed_doc)
                    
            processed[collection] = processed_docs
            
        return processed
    
    @time_operation
    def retrieve_template_examples(self, template_id: str, threat_type: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve template examples for a specific template and threat type.
        
        Args:
            template_id: ID of the template
            threat_type: Optional specific threat type to focus on
            
        Returns:
            List of example documents
        """
        query = f"template example for {template_id}"
        
        if threat_type:
            query += f" {threat_type}"
            
        # Search in templates collection
        results = vector_store.search(
            collection_name="templates",
            query=query,
            filter_metadata={"type": "example"},
            limit=2
        )
        
        return results
    
    @time_operation
    def retrieve_threat_info(self, threat_types: List[str], limit: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve detailed information about specific threat types.
        
        Args:
            threat_types: List of threat types to retrieve info about
            limit: Maximum results per threat type
            
        Returns:
            Dictionary mapping threat types to threat documents
        """
        threat_info = {}
        
        for threat_type in threat_types:
            # Search for this threat type
            results = vector_store.search(
                collection_name="threats",
                query=threat_type,
                filter_metadata={"category": threat_type} if threat_type else None,
                limit=limit
            )
            
            threat_info[threat_type] = results
            
        return threat_info
    
    def combine_retrieval_results(self, 
                                strategic_context: Dict[str, Any],
                                template_examples: List[Dict[str, Any]],
                                threat_info: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Combine all retrieval results into a unified context for generation.
        
        Args:
            strategic_context: Results from general strategic query
            template_examples: Template examples
            threat_info: Threat information
            
        Returns:
            Combined context dictionary
        """
        combined = {
            "strategic_context": strategic_context,
            "template_examples": template_examples,
            "threat_info": threat_info
        }
        
        # Calculate some statistics for logging
        total_docs = (
            sum(len(docs) for docs in strategic_context.get("documents", {}).values()) +
            len(template_examples) +
            sum(len(docs) for docs in threat_info.values())
        )
        
        system_logger.info(f"Combined {total_docs} documents for context generation")
        
        return combined
    
    def format_retrieved_content_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format the retrieved context into a string suitable for inclusion in a prompt.
        
        Args:
            context: The combined context from retrieval
            
        Returns:
            Formatted string for inclusion in prompt
        """
        prompt_parts = []
        
        # Format strategic context
        if "strategic_context" in context and "documents" in context["strategic_context"]:
            prompt_parts.append("# RETRIEVED CONTENT")
            
            # Papers (research)
            if "papers" in context["strategic_context"]["documents"]:
                papers = context["strategic_context"]["documents"]["papers"]
                if papers:
                    prompt_parts.append("\n## RESEARCH PAPERS")
                    for i, paper in enumerate(papers, 1):
                        content = paper.get("content", {})
                        title = content.get("title", f"Paper {i}")
                        text = content.get("content", "")
                        
                        prompt_parts.append(f"\n### {title}")
                        prompt_parts.append(text[:2000] + "..." if len(text) > 2000 else text)
            
            # Templates
            if "templates" in context["strategic_context"]["documents"]:
                templates = context["strategic_context"]["documents"]["templates"]
                if templates:
                    prompt_parts.append("\n## TEMPLATES")
                    for i, template in enumerate(templates, 1):
                        content = template.get("content", {})
                        title = content.get("title", f"Template {i}")
                        description = content.get("description", "")
                        text = content.get("content", "")
                        
                        prompt_parts.append(f"\n### {title}")
                        if description:
                            prompt_parts.append(description)
                        prompt_parts.append(text[:2000] + "..." if len(text) > 2000 else text)
            
            # Threats
            if "threats" in context["strategic_context"]["documents"]:
                threats = context["strategic_context"]["documents"]["threats"]
                if threats:
                    prompt_parts.append("\n## THREAT VECTORS")
                    for i, threat in enumerate(threats, 1):
                        content = threat.get("content", {})
                        title = content.get("title", f"Threat {i}")
                        desc = content.get("description", "")
                        impact = content.get("impact", "")
                        
                        prompt_parts.append(f"\n### {title}")
                        if desc:
                            prompt_parts.append(f"Description: {desc}")
                        if impact:
                            prompt_parts.append(f"Impact: {impact}")
                        
                        # Add mitigations if available
                        mitigations = content.get("mitigations", [])
                        if mitigations:
                            prompt_parts.append("Mitigations:")
                            for j, mitigation in enumerate(mitigations, 1):
                                prompt_parts.append(f"{j}. {mitigation}")
        
        # Format template examples
        if "template_examples" in context and context["template_examples"]:
            prompt_parts.append("\n## TEMPLATE EXAMPLES")
            for i, example in enumerate(context["template_examples"], 1):
                content = example.get("content", {})
                title = content.get("title", f"Example {i}")
                text = content.get("content", "")
                
                prompt_parts.append(f"\n### {title}")
                prompt_parts.append(text[:3000] + "..." if len(text) > 3000 else text)
        
        # Format threat info
        if "threat_info" in context:
            prompt_parts.append("\n## DETAILED THREAT INFORMATION")
            for threat_type, threats in context["threat_info"].items():
                if threats:
                    prompt_parts.append(f"\n### {threat_type.upper()}")
                    for i, threat in enumerate(threats, 1):
                        content = threat.get("content", {})
                        title = content.get("title", f"{threat_type} Threat {i}")
                        desc = content.get("description", "")
                        impact = content.get("impact", "")
                        
                        prompt_parts.append(f"\n#### {title}")
                        if desc:
                            prompt_parts.append(f"Description: {desc}")
                        if impact:
                            prompt_parts.append(f"Impact: {impact}")
                        
                        # Add mitigations if available
                        mitigations = content.get("mitigations", [])
                        if mitigations:
                            prompt_parts.append("Mitigations:")
                            for j, mitigation in enumerate(mitigations, 1):
                                prompt_parts.append(f"{j}. {mitigation}")
        
        # Format all parts into a single string
        formatted_content = "\n\n".join(prompt_parts)
        
        # Implement hallucination management if enabled
        if HALLUCINATION_MANAGEMENT["source_attribution"]:
            formatted_content += "\n\n# SOURCE ATTRIBUTION\n"
            formatted_content += "The information provided above comes from the following sources:\n"
            
            # Add sources from strategic context
            if "strategic_context" in context and "documents" in context["strategic_context"]:
                for collection, docs in context["strategic_context"]["documents"].items():
                    for doc in docs:
                        metadata = doc.get("metadata", {})
                        source = metadata.get("source", "Unknown source")
                        title = metadata.get("title", doc.get("id", "Untitled document"))
                        formatted_content += f"- {title} ({source})\n"
            
            # Add sources from template examples
            if "template_examples" in context and context["template_examples"]:
                for example in context["template_examples"]:
                    metadata = example.get("metadata", {})
                    source = metadata.get("source", "Unknown source")
                    title = metadata.get("title", example.get("id", "Untitled example"))
                    formatted_content += f"- {title} ({source})\n"
            
            # Add sources from threat info
            if "threat_info" in context:
                for threat_type, threats in context["threat_info"].items():
                    for threat in threats:
                        metadata = threat.get("metadata", {})
                        source = metadata.get("source", "Unknown source")
                        title = metadata.get("title", threat.get("id", "Untitled threat"))
                        formatted_content += f"- {title} ({source})\n"
        
        return formatted_content
    
    def extract_relevant_threat_patterns(self, strategic_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant threat patterns from the strategic context.
        
        Args:
            strategic_context: The strategic context from retrieval
            
        Returns:
            Dictionary of threat patterns
        """
        patterns = {}
        
        # Extract patterns from threat documents
        if "documents" in strategic_context and "threats" in strategic_context["documents"]:
            threats = strategic_context["documents"]["threats"]
            
            for threat in threats:
                content = threat.get("content", {})
                
                # For dictionary content
                if isinstance(content, dict):
                    threat_type = content.get("type", "unknown")
                    
                    if threat_type not in patterns:
                        patterns[threat_type] = []
                    
                    patterns[threat_type].append({
                        "title": content.get("title", "Unnamed threat"),
                        "description": content.get("description", ""),
                        "impact": content.get("impact", ""),
                        "mitigations": content.get("mitigations", [])
                    })
        
        return patterns
    
    def create_attribution_metadata(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create attribution metadata for the sources used in generation.
        This helps with hallucination management by tracking information sources.
        
        Args:
            context: The combined context from retrieval
            
        Returns:
            List of attribution metadata dictionaries
        """
        sources = []
        
        # Add sources from strategic context
        if "strategic_context" in context and "documents" in context["strategic_context"]:
            for collection, docs in context["strategic_context"]["documents"].items():
                for doc in docs:
                    metadata = doc.get("metadata", {})
                    source = {
                        "id": doc.get("id", ""),
                        "title": metadata.get("title", "Untitled document"),
                        "source": metadata.get("source", "Unknown source"),
                        "type": collection,
                        "similarity": doc.get("similarity", None)
                    }
                    sources.append(source)
        
        # Add sources from template examples
        if "template_examples" in context and context["template_examples"]:
            for example in context["template_examples"]:
                metadata = example.get("metadata", {})
                source = {
                    "id": example.get("id", ""),
                    "title": metadata.get("title", "Untitled example"),
                    "source": metadata.get("source", "Unknown source"),
                    "type": "template_example",
                    "similarity": example.get("similarity", None)
                }
                sources.append(source)
        
        # Add sources from threat info
        if "threat_info" in context:
            for threat_type, threats in context["threat_info"].items():
                for threat in threats:
                    metadata = threat.get("metadata", {})
                    source = {
                        "id": threat.get("id", ""),
                        "title": metadata.get("title", "Untitled threat"),
                        "source": metadata.get("source", "Unknown source"),
                        "type": "threat_info",
                        "subtype": threat_type,
                        "similarity": threat.get("similarity", None)
                    }
                    sources.append(source)
        
        return sources

# Create a singleton instance
rag_controller = RAGController()