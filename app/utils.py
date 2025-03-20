"""
Utility functions for the Security Script Generator application.
"""

import logging
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from app.config import SYSTEM_LOG_PATH, CHAT_LOG_PATH, GENERATION_LOG_PATH, LOG_LEVEL

# Set up logging
def setup_logger(name: str, log_file: Path, level: str = LOG_LEVEL) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    log_level = getattr(logging, level.upper())
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # File handler for persistent logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Set up system logger
system_logger = setup_logger('system', SYSTEM_LOG_PATH / f"system_{datetime.now().strftime('%Y%m%d')}.log")

# Generate a unique ID for each session
def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())

# Log chat messages
def log_chat_message(session_id: str, role: str, content: str, timestamp: Optional[str] = None) -> None:
    """Log a chat message to a session-specific file."""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    log_file = CHAT_LOG_PATH / f"chat_{session_id}.jsonl"
    
    log_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "role": role,
        "content": content
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

# Log script generation
def log_script_generation(session_id: str, context: Dict[str, Any], output: str) -> None:
    """Log script generation details."""
    timestamp = datetime.now().isoformat()
    log_file = GENERATION_LOG_PATH / f"generation_{session_id}.json"
    
    log_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "context": context,
        "output": output
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)

# Load the conversation history
def load_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """Load conversation history from the log file."""
    log_file = CHAT_LOG_PATH / f"chat_{session_id}.jsonl"
    history = []
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
    
    return history

# Utility function for timing operations
def time_operation(func):
    """Decorator to time function execution."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        system_logger.debug(f"Function {func.__name__} took {end_time - start_time:.4f} seconds to execute")
        return result
    return wrapper

# Sanitize user input
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Basic sanitization to remove potential script tags
    sanitized = text.replace('<script>', '').replace('</script>', '')
    return sanitized

# Format text as markdown
def format_as_markdown(script_content: Dict[str, str]) -> str:
    """Format the script content as a Markdown document."""
    markdown = "# Information Security Training Script\n\n"
    
    for section, content in script_content.items():
        if section == "metadata":
            markdown += f"## Metadata\n\n"
            for key, value in content.items():
                markdown += f"- **{key}**: {value}\n"
            markdown += "\n"
        else:
            title = content.get("title", section.replace("_", " ").title())
            markdown += f"## {title}\n\n"
            markdown += f"{content.get('content', '')}\n\n"
    
    return markdown

# Validation functions
def validate_strategic_responses(responses: Dict[str, Any]) -> List[str]:
    """Validate strategic question responses for completeness and correctness."""
    errors = []
    
    # Check required fields
    required_fields = ["facility_type", "target_audience", "duration", "focus_threats"]
    for field in required_fields:
        if field not in responses or not responses[field]:
            errors.append(f"Missing required information: {field}")
    
    # Validate duration
    if "duration" in responses:
        try:
            duration = int(responses["duration"])
            if duration < 15 or duration > 180:
                errors.append("Duration must be between 15 and 180 minutes")
        except (ValueError, TypeError):
            errors.append("Duration must be a number")
    
    return errors

# Hallucination detection support
def mark_uncertain_content(text: str, confidence_threshold: float = 0.7) -> str:
    """
    Mark content that might be uncertain based on certain markers.
    This is a simple implementation and would need to be expanded for production use.
    """
    uncertainty_markers = [
        "I believe", "I think", "possibly", "might be", "could be", 
        "perhaps", "may", "potentially", "not sure", "uncertain"
    ]
    
    # Simple approach - highlight text with uncertainty markers
    highlighted_text = text
    for marker in uncertainty_markers:
        highlighted_text = highlighted_text.replace(
            f" {marker} ", 
            f" [UNCERTAIN: {marker}] "
        )
    
    return highlighted_text

def generate_source_attribution(sources: List[Dict[str, Any]]) -> str:
    """Generate source attribution section for the script."""
    if not sources:
        return ""
    
    attribution = "## Quellen\n\n"
    for i, source in enumerate(sources, 1):
        attribution += f"{i}. {source.get('title', 'Unbekannte Quelle')}"
        if "author" in source:
            attribution += f" (Autor: {source['author']})"
        if "date" in source:
            attribution += f", {source['date']}"
        attribution += "\n"
    
    return attribution