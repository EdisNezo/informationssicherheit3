"""
Dialogue manager module for handling conversation flow.
This module manages the state of the conversation and determines the next steps.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

from app.utils import system_logger
from app.chatbot.questions import get_strategic_questions, get_contextual_questions, get_clarification_questions
from app.config import STRATEGIC_QUESTIONS

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
            "next_question_index": 0,
            "strategic_questions": get_strategic_questions(),
            "contextual_questions": [],
            "asked_questions": [],
            "responses": {},
            "missing_information": [],
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
        
        # Add to asked questions if not already there
        if question_id not in dialogue_state["asked_questions"]:
            dialogue_state["asked_questions"].append(question_id)
        
        # Update timestamp
        dialogue_state["last_updated"] = datetime.now().isoformat()
        
        # If we just completed strategic questions, generate contextual questions
        if question_id.startswith("clarify_") or len(dialogue_state["asked_questions"]) >= len(dialogue_state["strategic_questions"]):
            self._update_contextual_questions(session_id)
            
        return dialogue_state
    
    def _update_contextual_questions(self, session_id: str) -> None:
        """Update the contextual questions based on strategic responses."""
        dialogue_state = self.dialogue_states[session_id]
        responses = dialogue_state["responses"]
        
        # Extract key information
        facility_type = responses.get("facility_type", "")
        
        # Handle target_audience which might be a string or a list
        target_audience_raw = responses.get("target_audience", "")
        if isinstance(target_audience_raw, list):
            target_audience = target_audience_raw
        else:
            # Try to parse it as a comma-separated list
            target_audience = [item.strip() for item in target_audience_raw.split(",")]
        
        # Handle focus_threats which might be a string or a list
        focus_threats_raw = responses.get("focus_threats", "")
        if isinstance(focus_threats_raw, list):
            focus_threats = focus_threats_raw
        else:
            # Try to parse it as a comma-separated list
            focus_threats = [item.strip() for item in focus_threats_raw.split(",")]
        
        # Generate contextual questions
        contextual_questions = get_contextual_questions(
            facility_type=facility_type,
            target_audience=target_audience,
            focus_threats=focus_threats
        )
        
        # Update the dialogue state
        dialogue_state["contextual_questions"] = contextual_questions
    
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
        
        # If we're in the introduction stage, move to strategic questions
        if current_stage == "introduction":
            dialogue_state["current_stage"] = "strategic_questions"
            return self._get_next_strategic_question(session_id)
        
        # If we're in the strategic questions stage
        elif current_stage == "strategic_questions":
            # Check if we have more strategic questions
            next_question = self._get_next_strategic_question(session_id)
            if next_question:
                return next_question
            
            # If no more strategic questions, check for missing information
            self._check_for_missing_information(session_id)
            missing_info = dialogue_state["missing_information"]
            
            if missing_info:
                # Move to clarification stage
                dialogue_state["current_stage"] = "clarification"
                return self._get_next_clarification_question(session_id)
            
            # If no missing information, move to contextual questions
            dialogue_state["current_stage"] = "contextual_questions"
            return self._get_next_contextual_question(session_id)
        
        # If we're in the clarification stage
        elif current_stage == "clarification":
            # Check if we have more clarification questions
            next_question = self._get_next_clarification_question(session_id)
            if next_question:
                return next_question
            
            # If no more clarification questions, check for missing information again
            self._check_for_missing_information(session_id)
            missing_info = dialogue_state["missing_information"]
            
            if missing_info:
                # Stay in clarification stage
                return self._get_next_clarification_question(session_id)
            
            # If no missing information, move to contextual questions
            dialogue_state["current_stage"] = "contextual_questions"
            return self._get_next_contextual_question(session_id)
        
        # If we're in the contextual questions stage
        elif current_stage == "contextual_questions":
            # Check if we have more contextual questions
            next_question = self._get_next_contextual_question(session_id)
            if next_question:
                return next_question
            
            # If no more contextual questions, move to summary
            dialogue_state["current_stage"] = "summary"
            return None  # Signal that we're ready for a summary
        
        # If we're in the summary stage
        elif current_stage == "summary":
            # Check if we need any revisions
            if "needs_revision" in dialogue_state and dialogue_state["needs_revision"]:
                dialogue_state["current_stage"] = "revision"
                return None  # Signal that we're ready for revision instructions
            
            # If no revisions needed, move to complete
            dialogue_state["current_stage"] = "complete"
            return None  # Signal that we're ready for completion
        
        return None
    
    def _get_next_strategic_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next strategic question to ask."""
        dialogue_state = self.dialogue_states[session_id]
        strategic_questions = dialogue_state["strategic_questions"]
        next_index = dialogue_state["next_question_index"]
        
        # Check if we have more questions
        if next_index >= len(strategic_questions):
            return None
        
        # Get the next question
        next_question = strategic_questions[next_index]
        
        # Increment the index for next time
        dialogue_state["next_question_index"] = next_index + 1
        
        return next_question
    
    def _get_next_contextual_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next contextual question to ask."""
        dialogue_state = self.dialogue_states[session_id]
        contextual_questions = dialogue_state.get("contextual_questions", [])
        asked_questions = dialogue_state["asked_questions"]
        
        # Find the first question that hasn't been asked
        for question in contextual_questions:
            if question["id"] not in asked_questions:
                return question
        
        return None
    
    def _get_next_clarification_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next clarification question to ask."""
        dialogue_state = self.dialogue_states[session_id]
        missing_info = dialogue_state["missing_information"]
        asked_questions = dialogue_state["asked_questions"]
        
        # Get clarification questions for missing fields
        clarification_questions = get_clarification_questions(missing_info)
        
        # Find the first question that hasn't been asked
        for question in clarification_questions:
            if question["id"] not in asked_questions:
                return question
        
        return None
    
    def _check_for_missing_information(self, session_id: str) -> None:
        """Check for missing required information and update dialogue state."""
        dialogue_state = self.dialogue_states[session_id]
        responses = dialogue_state["responses"]
        missing_info = []
        
        # Check each required field
        required_fields = ["facility_type", "target_audience", "duration", "focus_threats"]
        for field in required_fields:
            if field not in responses or not responses[field]:
                missing_info.append(field)
        
        dialogue_state["missing_information"] = missing_info
    
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
        
        for question in dialogue_state["strategic_questions"]:
            question_id = question["id"]
            question_text = question["question"]
            
            if question_id in dialogue_state["responses"]:
                response = dialogue_state["responses"][question_id]
                response_summary[question_text] = response
        
        for question in dialogue_state["contextual_questions"]:
            question_id = question["id"]
            question_text = question["question"]
            
            if question_id in dialogue_state["responses"]:
                response = dialogue_state["responses"][question_id]
                response_summary[question_text] = response
        
        return {
            "stage": dialogue_state["current_stage"],
            "responses": response_summary,
            "missing_information": dialogue_state["missing_information"],
            "questions_asked": len(dialogue_state["asked_questions"]),
            "last_updated": dialogue_state["last_updated"]
        }
    
    def flag_for_revision(self, session_id: str, revision_request: str) -> None:
        """
        Flag a dialogue for revision.
        
        Args:
            session_id: Session ID
            revision_request: Description of the requested revision
        """
        if session_id in self.dialogue_states:
            dialogue_state = self.dialogue_states[session_id]
            dialogue_state["needs_revision"] = True
            dialogue_state["revision_request"] = revision_request
            dialogue_state["current_stage"] = "revision"
    
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