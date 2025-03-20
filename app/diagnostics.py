# Create a new file: app/diagnostics.py

import logging
import traceback
import re
import json
from pathlib import Path

# Set up a specialized logger
diagnostics_logger = logging.getLogger("format_diagnostics")
handler = logging.FileHandler("format_error_diagnostics.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
diagnostics_logger.addHandler(handler)
diagnostics_logger.setLevel(logging.DEBUG)

def inspect_string(string_value, context_name="unknown"):
    """Deeply inspect a string for potential format specifiers."""
    if not isinstance(string_value, str):
        diagnostics_logger.info(f"Context '{context_name}' is not a string: {type(string_value)}")
        return
    
    # Look for potential format specifiers
    potential_format_specifiers = re.findall(r'%[^%]', string_value)
    
    if potential_format_specifiers:
        diagnostics_logger.warning(f"Found potential format specifiers in '{context_name}': {potential_format_specifiers}")
        # Log surrounding context for each specifier
        for specifier in potential_format_specifiers:
            position = string_value.find(specifier)
            start = max(0, position - 20)
            end = min(len(string_value), position + 20)
            context = string_value[start:end]
            diagnostics_logger.warning(f"Context around '{specifier}': '...{context}...'")

def safe_format(template_string, **kwargs):
    """
    A completely safe formatting function that will never raise format errors.
    
    This replaces Python's string formatting completely with a custom implementation
    that doesn't use any of Python's built-in formatting mechanisms.
    """
    # First, escape all % signs by doubling them
    result = template_string.replace("%", "%%")
    
    # Then manually replace each {key} with its value
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        if placeholder in result:
            # Convert value to string to be safe
            str_value = str(value) if value is not None else ""
            result = result.replace(placeholder, str_value)
    
    return result

def fix_prompt(prompt):
    """
    Fix any potential format specifiers in a prompt string.
    
    This function simply escapes all % signs to prevent format errors.
    """
    if not isinstance(prompt, str):
        return str(prompt) if prompt is not None else ""
    
    # Replace lone % with %% to escape them
    return prompt.replace("%", "%%")

class SafeFormatter:
    """
    A safe string formatting class that replaces Python's built-in formatting.
    """
    
    @staticmethod
    def format(template, **kwargs):
        """Safely format a string with named placeholders."""
        return safe_format(template, **kwargs)
    
    @staticmethod
    def safe_json_dumps(obj, **kwargs):
        """Safely convert an object to JSON without risking format specifiers."""
        # First get the JSON string
        json_str = json.dumps(obj, **kwargs)
        # Then escape any % characters
        return json_str.replace("%", "%%")