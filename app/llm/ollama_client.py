"""
Ollama client module for interacting with the Ollama LLM service.
This module handles sending prompts to the LLM and processing the responses.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Union, Generator
import time

from app.config import OLLAMA_HOST, OLLAMA_MODEL
from app.utils import system_logger, time_operation

class OllamaClient:
    """Client for interacting with the Ollama LLM service."""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        """
        Initialize the Ollama client.
        
        Args:
            host: Ollama API host URL
            model: Model name to use
        """
        self.host = host
        self.model = model
        self.base_url = f"{host}/api"
        system_logger.info(f"Initialized OllamaClient with host: {host}, model: {model}")
    
    def _check_health(self) -> bool:
        """Check if the Ollama service is healthy and available."""
        try:
            response = requests.get(f"{self.host}")
            return response.status_code == 200
        except Exception as e:
            system_logger.error(f"Ollama health check failed: {e}")
            return False
    
    @time_operation
    def generate(self, 
            prompt: str, 
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Generate text from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Generated text or generator yielding text chunks if streaming
        """
        url = f"{self.base_url}/generate"
        
        # Prepare request data
        request_data = {
            "model": self.model,
            "prompt": prompt,  # Don't modify the prompt string
            "temperature": temperature,
            "stream": stream
        }
        
        # Add optional parameters
        if system_prompt:
            request_data["system"] = system_prompt
            
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        try:
            # For streaming, return a generator
            if stream:
                return self._stream_response(url, request_data)
            
            # For non-streaming, return the complete response
            response = requests.post(url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Log token usage if available
            if "eval_count" in result:
                system_logger.info(f"Generated {result['eval_count']} tokens")
                
            return generated_text
            
        except requests.exceptions.RequestException as e:
            system_logger.error(f"Error generating text: {e}")
            if stream:
                # Return an error message via the generator
                def error_generator():
                    yield f"Error generating text: {e}"
                return error_generator()
            else:
                return f"Error generating text: {e}"
    
    def _stream_response(self, url: str, request_data: Dict[str, Any]) -> Generator[str, None, None]:
        """Stream the response from Ollama."""
        try:
            with requests.post(url, json=request_data, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                                
                            # Check for completion
                            if chunk.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            yield f"Error parsing response: {line}"
                            
        except requests.exceptions.RequestException as e:
            yield f"Error streaming response: {e}"
    
    @time_operation
    def chat(self, 
            messages: List[Dict[str, str]], 
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Generate text using the chat endpoint.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Generated text or generator yielding text chunks if streaming
        """
        url = f"{self.base_url}/chat"
        
        # Prepare request data
        request_data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add optional parameters
        if system_prompt:
            request_data["system"] = system_prompt
            
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        try:
            # For streaming, return a generator
            if stream:
                return self._stream_chat_response(url, request_data)
            
            # For non-streaming, return the complete response
            response = requests.post(url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            message = result.get("message", {})
            generated_text = message.get("content", "")
            
            # Log token usage if available
            if "eval_count" in result:
                system_logger.info(f"Generated {result['eval_count']} tokens")
                
            return generated_text
            
        except requests.exceptions.RequestException as e:
            system_logger.error(f"Error in chat completion: {e}")
            if stream:
                # Return an error message via the generator
                def error_generator():
                    yield f"Error in chat completion: {e}"
                return error_generator()
            else:
                return f"Error in chat completion: {e}"
    
    def _stream_chat_response(self, url: str, request_data: Dict[str, Any]) -> Generator[str, None, None]:
        """Stream the chat response from Ollama."""
        try:
            with requests.post(url, json=request_data, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            message = chunk.get("message", {})
                            if "content" in message:
                                yield message["content"]
                                
                            # Check for completion
                            if chunk.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            yield f"Error parsing chat response: {line}"
                            
        except requests.exceptions.RequestException as e:
            yield f"Error streaming chat response: {e}"
    
    def get_available_models(self) -> List[str]:
        """Get a list of available models from Ollama."""
        url = f"{self.base_url}/tags"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            models = [model["name"] for model in result.get("models", [])]
            
            return models
            
        except requests.exceptions.RequestException as e:
            system_logger.error(f"Error getting available models: {e}")
            return []
    
    def check_factuality(self, statement: str, context: str) -> Dict[str, Any]:
        """
        Check the factuality of a statement against the provided context.
        This is part of the hallucination management strategy.
        
        Args:
            statement: Statement to check
            context: Context to check against
            
        Returns:
            Dictionary with factuality score and explanation
        """
        # Create a factuality-checking prompt
        prompt = f"""
        You are an expert fact-checker. Your task is to determine if the following statement is supported by the provided context.
        
        STATEMENT:
        {statement}
        
        CONTEXT:
        {context}
        
        Rate the factuality of the statement on a scale of 0-10, where:
        0: Completely contradicts the context
        5: Neither supported nor contradicted by the context
        10: Completely supported by the context
        
        Provide your rating and a brief explanation in JSON format:
        {{
            "rating": <your rating>,
            "explanation": "<your explanation>"
        }}
        
        Response (JSON only):
        """
        
        try:
            response = self.generate(prompt, temperature=0.2)
            
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                return {
                    "rating": 5,  # Neutral when parsing fails
                    "explanation": "Could not parse factuality check response."
                }
                
        except Exception as e:
            system_logger.error(f"Error checking factuality: {e}")
            return {
                "rating": 5,  # Neutral on error
                "explanation": f"Error checking factuality: {e}"
            }

# Create a singleton instance
ollama_client = OllamaClient()