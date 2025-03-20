"""
Dialogue manager module for handling conversation flow.
This module manages the state of the conversation and determines the next steps.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

from app.utils import system_logger
from app.chatbot.questions import get_strategic_questions, get_template_question, get_section_keys

class DialogueManager:
    """Manager for handling the dialogue flow with users."""
    
    def __init__(self):
        """Initialize the dialogue manager."""
        system_logger.info("Initializing DialogueManager")
        self.dialogue_states = {}
    
    def initialize_dialogue(self, session_id: str) -> Dict[str, Any]:
        """
        Initialize a new dialogue for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Initial dialogue state
        """
        dialogue_state = {
            "current_stage": "introduction",
            "current_step": 0,
            "context_questions": get_strategic_questions(),
            "section_keys": get_section_keys(),
            "current_section_index": -1,  # Start with -1 to indicate we're in the context questions phase
            "responses": {},
            "last_updated": datetime.now().isoformat()
        }
        
        self.dialogue_states[session_id] = dialogue_state
        return dialogue_state
    
    def get_dialogue_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current dialogue state for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dialogue state dictionary or None if not found
        """
        return self.dialogue_states.get(session_id)
    
    def update_dialogue_state(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update the dialogue state for a session.
        
        Args:
            session_id: Session ID
            updates: Dictionary of updates to apply
            
        Returns:
            Updated dialogue state or None if session not found
        """
        if session_id not in self.dialogue_states:
            return None
        
        # Apply updates
        for key, value in updates.items():
            self.dialogue_states[session_id][key] = value
        
        # Update last_updated timestamp
        self.dialogue_states[session_id]["last_updated"] = datetime.now().isoformat()
        
        return self.dialogue_states[session_id]
    
    def process_response(self, session_id: str, question_id: str, response: str) -> Dict[str, Any]:
        """
        Process a user's response to a question.
        
        Args:
            session_id: Session ID
            question_id: ID of the question being answered
            response: User's response
            
        Returns:
            Updated dialogue state
        """
        if session_id not in self.dialogue_states:
            return self.initialize_dialogue(session_id)
        
        dialogue_state = self.dialogue_states[session_id]
        
        # Store the response
        dialogue_state["responses"][question_id] = response
        
        # Update timestamp
        dialogue_state["last_updated"] = datetime.now().isoformat()
            
        return dialogue_state
    
    def advance_dialogue(self, session_id: str) -> None:
        """
        Advance the dialogue to the next step.
        
        Args:
            session_id: Session ID
        """
        if session_id not in self.dialogue_states:
            return
            
        dialogue_state = self.dialogue_states[session_id]
        current_stage = dialogue_state["current_stage"]
        
        # If we're in the introduction stage, move to context questions
        if current_stage == "introduction":
            dialogue_state["current_stage"] = "context_questions"
            dialogue_state["current_step"] = 0
            return
            
        # If we're in the context questions stage
        elif current_stage == "context_questions":
            # Increment the step
            dialogue_state["current_step"] += 1
            
            # If we've asked all context questions, move to template questions
            if dialogue_state["current_step"] >= len(dialogue_state["context_questions"]):
                dialogue_state["current_stage"] = "template_questions"
                dialogue_state["current_section_index"] = 0
                dialogue_state["current_step"] = 0
            return
                
        # If we're in the template questions stage
        elif current_stage == "template_questions":
            # Increment the section index
            dialogue_state["current_section_index"] += 1
            
            # If we've asked all template questions, move to summary
            if dialogue_state["current_section_index"] >= len(dialogue_state["section_keys"]):
                dialogue_state["current_stage"] = "summary"
            return
                
        # If we're in the summary stage, move to complete
        elif current_stage == "summary":
            dialogue_state["current_stage"] = "complete"
            return
    
    def get_next_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next question to ask in the dialogue.
        
        Args:
            session_id: Session ID
            
        Returns:
            Next question dictionary or None if no more questions
        """
        if session_id not in self.dialogue_states:
            return None
        
        dialogue_state = self.dialogue_states[session_id]
        current_stage = dialogue_state["current_stage"]
        
        # If we're in the introduction stage, there's no question to ask yet
        if current_stage == "introduction":
            return None
        
        # If we're in the context questions stage
        elif current_stage == "context_questions":
            return self._get_next_context_question(session_id)
        
        # If we're in the template questions stage
        elif current_stage == "template_questions":
            return self._get_next_template_question(session_id)
        
        # If we're in the summary or complete stage, there are no more questions
        return None
    
    def _get_next_context_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next context question to ask."""
        dialogue_state = self.dialogue_states[session_id]
        current_step = dialogue_state["current_step"]
        context_questions = dialogue_state["context_questions"]
        
        # Check if we have more questions
        if current_step >= len(context_questions):
            return None
        
        # Get the next question
        next_question = context_questions[current_step]
        
        return next_question
    
    def _get_next_template_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next template question to ask."""
        dialogue_state = self.dialogue_states[session_id]
        current_section_index = dialogue_state["current_section_index"]
        section_keys = dialogue_state["section_keys"]
        
        # Check if we have more sections
        if current_section_index >= len(section_keys):
            return None
        
        # Get the current section key
        section_key = section_keys[current_section_index]
        
        # Get the template question for this section
        template_question = get_template_question(section_key, dialogue_state["responses"])
        
        # Add section information
        template_question["section_key"] = section_key
        template_question["id"] = f"template_{section_key}"
        
        return template_question
    
    def is_dialogue_complete(self, session_id: str) -> bool:
        """
        Check if the dialogue is complete.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if the dialogue is complete, False otherwise
        """
        if session_id not in self.dialogue_states:
            return False
            
        dialogue_state = self.dialogue_states[session_id]
        return dialogue_state["current_stage"] == "complete"
    
    def get_script_generation_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get the context for script generation.
        
        Args:
            session_id: Session ID
            
        Returns:
            Context dictionary for script generation
        """
        if session_id not in self.dialogue_states:
            return {}
            
        dialogue_state = self.dialogue_states[session_id]
        
        # Create a context dictionary with all responses
        context = dialogue_state["responses"].copy()
        
        # Add some metadata
        context["generated_at"] = datetime.now().isoformat()
        context["dialogue_complete"] = self.is_dialogue_complete(session_id)
        
        return context
    
    def get_dialogue_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a summary of the dialogue state.
        
        Args:
            session_id: Session ID
            
        Returns:
            Summary dictionary
        """
        if session_id not in self.dialogue_states:
            return {"error": "Session not found"}
        
        dialogue_state = self.dialogue_states[session_id]
        
        # Create a summary of responses
        response_summary = {}
        
        # Process context question responses
        for question in dialogue_state["context_questions"]:
            question_id = question["id"]
            question_text = question["question"]
            
            if question_id in dialogue_state["responses"]:
                response = dialogue_state["responses"][question_id]
                response_summary[question_text] = response
        
        # Process template question responses
        section_keys = dialogue_state["section_keys"]
        for section_key in section_keys:
            template_question_id = f"template_{section_key}"
            if template_question_id in dialogue_state["responses"]:
                # Get the original question text
                template_question = get_template_question(section_key, dialogue_state["responses"])
                question_text = template_question["question"]
                
                response = dialogue_state["responses"][template_question_id]
                response_summary[question_text] = response
        
        return {
            "stage": dialogue_state["current_stage"],
            "responses": response_summary,
            "questions_asked": len(response_summary),
            "last_updated": dialogue_state["last_updated"]
        }
    
    def clean_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired dialogue sessions.
        
        Args:
            max_age_hours: Maximum age in hours for a session
            
        Returns:
            Number of sessions removed
        """
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, dialogue_state in self.dialogue_states.items():
            last_updated = datetime.fromisoformat(dialogue_state["last_updated"])
            age_hours = (current_time - last_updated).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)
        
        # Remove expired sessions
        for session_id in sessions_to_remove:
            del self.dialogue_states[session_id]
        
        return len(sessions_to_remove)

# Create a singleton instance
dialogue_manager = DialogueManager()