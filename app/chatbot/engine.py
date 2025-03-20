"""
Chatbot engine module that manages the conversation with the user.
This module coordinates the question-answering process and maintains conversation state.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import json
import re
from datetime import datetime

from app.utils import system_logger, time_operation, generate_session_id, log_chat_message
from app.llm.ollama_client import ollama_client
from app.llm.prompt_builder import prompt_builder
from app.rag.controller import rag_controller
from app.chatbot.questions import get_strategic_questions
from app.config import STRATEGIC_QUESTIONS, TEMPLATE_STRUCTURE, HALLUCINATION_MANAGEMENT

class ChatbotEngine:
    """Engine for managing the chatbot's conversation with users."""
    
    def __init__(self):
        """Initialize the chatbot engine."""
        system_logger.info("Initializing ChatbotEngine")
        self.active_sessions = {}
    
    def create_session(self) -> str:
        """
        Create a new chat session.
        
        Returns:
            Session ID
        """
        session_id = generate_session_id()
        
        self.active_sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "strategic_responses": {},
            "current_question_index": 0,
            "stage": "introduction",
            "messages": [],
            "generated_script": None,
            "script_sections": {}
        }
        
        system_logger.info(f"Created new session with ID: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def get_introduction_message(self, session_id: str) -> str:
        """
        Get the introduction message for a new session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Introduction message
        """
        introduction = """
        Willkommen! Ich bin Ihr Assistent für die Erstellung von E-Learning-Inhalten zu Informationssicherheit.

        Um ein maßgeschneidertes Schulungsskript zu erstellen, werde ich Ihnen einige Fragen stellen. 
        Diese helfen mir, den Kontext, die Zielgruppe und die spezifischen Sicherheitsanforderungen Ihrer medizinischen Einrichtung zu verstehen.

        Lassen Sie uns beginnen!
        """
        
        # Add this message to the session history
        if session_id in self.active_sessions:
            self._add_message_to_session(session_id, "assistant", introduction)
        
        return introduction
    
    def _add_message_to_session(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            
            # Also log to file
            log_chat_message(session_id, role, content)
    
    @time_operation
    def process_message(self, session_id: str, message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            session_id: Session ID
            message: User message
            
        Returns:
            Chatbot response
        """
        if session_id not in self.active_sessions:
            system_logger.warning(f"Invalid session ID: {session_id}")
            return "Es scheint ein Problem mit Ihrer Sitzung zu geben. Bitte starten Sie eine neue Sitzung."
        
        # Add user message to history
        self._add_message_to_session(session_id, "user", message)
        
        # Get current session stage
        session = self.active_sessions[session_id]
        stage = session.get("stage", "introduction")
        
        # Process based on stage
        if stage == "introduction":
            # Move to question stage
            self.active_sessions[session_id]["stage"] = "strategic_questions"
            response = self._get_next_strategic_question(session_id)
            
        elif stage == "strategic_questions":
            # Process strategic question response
            response = self._process_strategic_question_response(session_id, message)
            
        elif stage == "clarification":
            # Process clarification response
            response = self._process_clarification_response(session_id, message)
            
        elif stage == "review":
            # Process review response
            response = self._process_review_response(session_id, message)
            
        elif stage == "script_generation":
            # Process script generation request
            response = self._process_script_generation_request(session_id, message)
            
        elif stage == "followup":
            # Process follow-up request
            response = self._process_followup_request(session_id, message)
            
        else:
            # Handle unexpected stage
            system_logger.error(f"Unexpected stage '{stage}' for session {session_id}")
            response = "Es ist ein Fehler aufgetreten. Bitte starten Sie eine neue Sitzung."
        
        # Add response to history
        self._add_message_to_session(session_id, "assistant", response)
        
        return response
    
    def _get_next_strategic_question(self, session_id: str) -> str:
        """Get the next strategic question to ask."""
        session = self.active_sessions[session_id]
        question_index = session.get("current_question_index", 0)
        
        # Get strategic questions
        strategic_questions = get_strategic_questions()
        
        # Check if we've asked all questions
        if question_index >= len(strategic_questions):
            # Move to review stage
            self.active_sessions[session_id]["stage"] = "review"
            return self._generate_review_summary(session_id)
        
        # Get the current question
        question = strategic_questions[question_index]
        
        # Get prompt for this question
        question_prompt = prompt_builder.build_strategic_question_prompt(question)
        
        # Format question nicely
        question_text = question.get("question", "")
        description = question.get("description", "")
        
        formatted_question = f"{question_text}\n\n{description}"
        
        return formatted_question
    
    def _process_strategic_question_response(self, session_id: str, message: str) -> str:
        """Process the user's response to a strategic question."""
        session = self.active_sessions[session_id]
        question_index = session.get("current_question_index", 0)
        
        # Get strategic questions
        strategic_questions = get_strategic_questions()
        current_question = strategic_questions[question_index]
        question_id = current_question.get("id", f"question_{question_index}")
        
        # Store the response
        session["strategic_responses"][question_id] = message
        
        # Increment question index
        session["current_question_index"] = question_index + 1
        
        # Get next question
        return self._get_next_strategic_question(session_id)
    
    def _process_clarification_response(self, session_id: str, message: str) -> str:
        """Process the user's response to a clarification request."""
        session = self.active_sessions[session_id]
        clarification_type = session.get("clarification_type", "")
        
        if clarification_type == "missing_info":
            # Update the missing information
            missing_field = session.get("missing_field", "")
            if missing_field:
                session["strategic_responses"][missing_field] = message
            
            # Move back to review stage
            session["stage"] = "review"
            return self._generate_review_summary(session_id)
        
        elif clarification_type == "confirm_generation":
            # Check if user confirms
            if re.search(r'\b(ja|yes|ok|okay|generieren|erstellen|generiere|beginnen?)\b', message.lower()):
                # Move to script generation stage
                session["stage"] = "script_generation"
                return self._generate_script(session_id)
            else:
                # Return to review stage
                session["stage"] = "review"
                return "In Ordnung. Lassen Sie mich wissen, welche Änderungen Sie vornehmen möchten, bevor wir das Skript generieren."
        
        else:
            # Default clarification handling
            session["stage"] = "review"
            return self._generate_review_summary(session_id)
    
    def _generate_review_summary(self, session_id: str) -> str:
        """Generate a summary of the collected information for review."""
        session = self.active_sessions[session_id]
        strategic_responses = session.get("strategic_responses", {})
        
        # Create a summary of collected information
        summary_parts = ["Vielen Dank für Ihre Antworten! Hier ist eine Zusammenfassung der Informationen, die ich gesammelt habe:\n"]
        
        # Add each piece of information
        for question in get_strategic_questions():
            question_id = question.get("id", "")
            question_text = question.get("question", "")
            
            if question_id in strategic_responses:
                response = strategic_responses[question_id]
                summary_parts.append(f"- {question_text}\n  {response}")
        
        # Ask for confirmation
        summary_parts.append("\nSind diese Informationen korrekt? Möchten Sie etwas ändern oder ergänzen, bevor ich das Skript erstelle?")
        
        # Set stage to review
        session["stage"] = "review"
        
        return "\n\n".join(summary_parts)
    
    def _process_review_response(self, session_id: str, message: str) -> str:
        """Process the user's response during the review stage."""
        session = self.active_sessions[session_id]
        
        # Check if user wants to proceed with generation
        if re.search(r'\b(ja|yes|ok|okay|generieren|erstellen|generiere|beginnen?)\b', message.lower()):
            # Move to clarification stage with confirmation type
            session["stage"] = "clarification"
            session["clarification_type"] = "confirm_generation"
            
            return "Ausgezeichnet! Ich werde nun das Schulungsskript basierend auf Ihren Anforderungen erstellen. Dies kann einen Moment dauern. Möchten Sie fortfahren?"
        
        # Check if user wants to change something
        elif re.search(r'\b(nein|no|ändern|änderung|anpassen|korrigieren)\b', message.lower()):
            # Try to identify what they want to change
            for question in get_strategic_questions():
                question_id = question.get("id", "")
                question_text = question.get("question", "")
                
                # Check if the message mentions keywords related to this question
                if any(keyword.lower() in message.lower() for keyword in question_text.split()):
                    # Move to clarification stage for this field
                    session["stage"] = "clarification"
                    session["clarification_type"] = "missing_info"
                    session["missing_field"] = question_id
                    
                    return f"Bitte geben Sie die aktualisierte Information für '{question_text}' ein:"
            
            # If no specific question is identified, ask for clarification
            return "Was genau möchten Sie ändern oder ergänzen? Bitte teilen Sie mir mit, welche Information aktualisiert werden soll."
        
        else:
            # Assume they want to add general information and proceed
            # Add this as a custom scenario
            session["strategic_responses"]["additional_info"] = message
            
            # Move to clarification stage with confirmation type
            session["stage"] = "clarification"
            session["clarification_type"] = "confirm_generation"
            
            return "Danke für die zusätzlichen Informationen! Möchten Sie jetzt das Schulungsskript generieren?"
    
    @time_operation
    def _generate_script(self, session_id: str) -> str:
        """Generate the complete training script."""
        from app.diagnostics import diagnostics_logger, fix_prompt
        
        session = self.active_sessions[session_id]
        strategic_responses = session.get("strategic_responses", {})
        
        # Log that we're starting generation
        diagnostics_logger.info(f"Starting script generation for session {session_id}")
        
        # Prepare the session context from strategic responses
        session_context = {}
        for question in get_strategic_questions():
            question_id = question.get("id", "")
            if question_id in strategic_responses:
                response = strategic_responses[question_id]
                session_context[question_id] = response
        
        diagnostics_logger.info(f"Session context prepared with keys: {list(session_context.keys())}")
        
        # Update the stage to indicate generation is in progress
        session["stage"] = "generating"
        
        try:
            # Retrieve relevant context from the RAG system
            query = f"Security training for {session_context.get('facility_type', 'medical facility')} focused on {session_context.get('focus_threats', 'security threats')}"
            strategic_context = rag_controller.retrieve_context(query, session_context)
            
            # Get template examples
            threats = session_context.get("focus_threats", [])
            if isinstance(threats, str):
                threats = [threats]
            main_threat = threats[0] if threats else "phishing"
            template_examples = rag_controller.retrieve_template_examples("seven_step", main_threat)
            
            # Get detailed threat info
            threat_info = rag_controller.retrieve_threat_info(threats)
            
            # Combine all retrieved information
            combined_context = rag_controller.combine_retrieval_results(
                strategic_context=strategic_context,
                template_examples=template_examples,
                threat_info=threat_info
            )
            
            formatted_context = rag_controller.format_retrieved_content_for_prompt(combined_context)
            diagnostics_logger.info(f"Formatted context length: {len(formatted_context)}")
            
            # Build the script generation prompt
            script_prompt = prompt_builder.build_script_generation_prompt(
                session_context=session_context,
                retrieved_context=formatted_context
            )
            diagnostics_logger.info(f"Built script generation prompt, length: {len(script_prompt)}")
            
            # Get system prompt
            system_prompt = prompt_builder.build_system_prompt()
            diagnostics_logger.info(f"Built system prompt, length: {len(system_prompt)}")
            
            # Generate the script
            diagnostics_logger.info("Calling ollama_client.generate")
            generated_script = ollama_client.generate(
                prompt=script_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            diagnostics_logger.info(f"Generation complete, script length: {len(generated_script) if isinstance(generated_script, str) else 'N/A'}")
            
            # Store the generated script
            session["generated_script"] = generated_script
            session["generation_context"] = {
                "session_context": session_context,
                "retrieved_context": formatted_context,
                "prompt": script_prompt,
                "sources": rag_controller.create_attribution_metadata(combined_context)
            }
            
            # Update stage
            session["stage"] = "followup"
            
            # Check for hallucinations if enabled
            if HALLUCINATION_MANAGEMENT["factuality_check"]:
                hallucination_check = self._check_for_hallucinations(session_id)
                if hallucination_check["has_hallucinations"]:
                    # Add hallucination warning
                    hallucination_warnings = "\n\n## Hinweis zu möglichen Halluzinationen\n"
                    hallucination_warnings += "Das generierte Skript könnte folgende unbestätigte Informationen enthalten:\n"
                    
                    for h in hallucination_check["hallucinations"]:
                        hallucination_warnings += f"- \"{h['text']}\": {h['reason']}\n"
                    
                    session["hallucination_warnings"] = hallucination_warnings
            
            # Format a response message about successful generation
            response = """
            Ich habe das Schulungsskript basierend auf Ihren Anforderungen erstellt!

            Das Skript folgt dem 7-Stufen-Template und wurde speziell für Ihre Anforderungen angepasst. Es enthält alle wichtigen Informationen zu den Sicherheitsbedrohungen, deren Erkennung, Auswirkungen und Gegenmaßnahmen.

            Möchten Sie das vollständige Skript sehen oder benötigen Sie Anpassungen in bestimmten Abschnitten?
            """
            
            return response
            
        except Exception as e:
            diagnostics_logger.error(f"Error in _generate_script: {str(e)}\n{traceback.format_exc()}")
            system_logger.error(f"Error generating script for session {session_id}: {e}")
            
            # Update stage to indicate failure
            session["stage"] = "review"
            
            return "Bei der Erstellung des Skripts ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut oder passen Sie Ihre Anforderungen an."
    
    def _check_for_hallucinations(self, session_id: str) -> Dict[str, Any]:
        """Check the generated script for potential hallucinations."""
        session = self.active_sessions[session_id]
        generated_script = session.get("generated_script", "")
        generation_context = session.get("generation_context", {})
        retrieved_context = generation_context.get("retrieved_context", "")
        
        # Build hallucination check prompt
        check_prompt = prompt_builder.build_hallucination_check_prompt(
            generated_content=generated_script,
            retrieved_context=retrieved_context
        )
        
        # Use a lower temperature for more deterministic output
        try:
            result = ollama_client.generate(check_prompt, temperature=0.2)
            
            # Extract JSON from result
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"has_hallucinations": False, "hallucinations": []}
                
        except Exception as e:
            system_logger.error(f"Error checking for hallucinations: {e}")
            return {"has_hallucinations": False, "hallucinations": []}
    
    def _process_script_generation_request(self, session_id: str, message: str) -> str:
        """Process a request to generate or modify the script."""
        session = self.active_sessions[session_id]
        
        # Check if we already have a generated script
        if not session.get("generated_script"):
            return self._generate_script(session_id)
        
        # Process request to modify or view the script
        if re.search(r'\b(anpassen|ändern|modifizieren)\b', message.lower()):
            # User wants to modify the script
            return "Welchen Teil des Skripts möchten Sie anpassen? Bitte geben Sie an, ob es sich um einen bestimmten Abschnitt handelt oder um allgemeine Änderungen."
        
        elif re.search(r'\b(sehen|anzeigen|zeigen)\b', message.lower()):
            # User wants to see the script
            return self.get_generated_script(session_id)
        
        else:
            # Default to showing the script
            return self.get_generated_script(session_id)
    
    def _process_followup_request(self, session_id: str, message: str) -> str:
        """Process follow-up requests after script generation."""
        session = self.active_sessions[session_id]
        
        # Check for common follow-up requests
        if re.search(r'\b(anpassen|ändern|modifizieren)\b', message.lower()):
            # User wants to modify the script
            return "Welchen Teil des Skripts möchten Sie anpassen? Bitte geben Sie an, ob es sich um einen bestimmten Abschnitt handelt oder um allgemeine Änderungen."
        
        elif re.search(r'\b(sehen|anzeigen|zeigen)\b', message.lower()):
            # User wants to see the script
            return self.get_generated_script(session_id)
        
        elif re.search(r'\b(speichern|exportieren|download)\b', message.lower()):
            # User wants to export/save the script
            return "Das Skript steht zum Herunterladen bereit. Sie können es über die Exportfunktion der Anwendung als Markdown-Datei speichern."
        
        elif re.search(r'\b(section|abschnitt|teil)\b', message.lower()):
            # User is asking about a specific section
            # Try to identify which section
            for section_key in TEMPLATE_STRUCTURE.keys():
                section_info = TEMPLATE_STRUCTURE[section_key]
                section_title = section_info.get("title", "")
                
                if section_title.lower() in message.lower() or section_key.lower() in message.lower():
                    # Extract this section from the script
                    return self._extract_section_from_script(session_id, section_key)
            
            # If no specific section identified
            return "Welchen Abschnitt des Skripts möchten Sie sehen? Bitte geben Sie den Namen des Abschnitts an (z.B. 'Threat Awareness', 'Tactic Choice', etc.)."
        
        else:
            # General follow-up response
            return "Wie kann ich Ihnen weiterhelfen? Möchten Sie das Skript sehen, bestimmte Abschnitte anpassen oder eine neue Anfrage starten?"
    
    def _extract_section_from_script(self, session_id: str, section_key: str) -> str:
        """Extract a specific section from the generated script."""
        session = self.active_sessions[session_id]
        generated_script = session.get("generated_script", "")
        
        # Get section title
        section_info = TEMPLATE_STRUCTURE.get(section_key, {})
        section_title = section_info.get("title", section_key.replace("_", " ").title())
        
        # Try to extract this section
        section_pattern = re.compile(f"#{{{1,3}}}\\s*{re.escape(section_title)}.*?(?=#{{{1,3}}}|$)", re.DOTALL)
        match = section_pattern.search(generated_script)
        
        if match:
            return f"Hier ist der Abschnitt '{section_title}':\n\n{match.group(0)}"
        else:
            return f"Der Abschnitt '{section_title}' konnte im generierten Skript nicht gefunden werden. Möchten Sie das vollständige Skript sehen?"
    
    def get_generated_script(self, session_id: str) -> str:
        """Get the generated script for a session."""
        session = self.active_sessions[session_id]
        generated_script = session.get("generated_script", "")
        
        if not generated_script:
            return "Es wurde noch kein Skript generiert. Möchten Sie jetzt ein Skript erstellen?"
        
        # Add hallucination warnings if any
        if "hallucination_warnings" in session:
            generated_script += session["hallucination_warnings"]
        
        return f"Hier ist das generierte Schulungsskript:\n\n{generated_script}"
    
    def customize_script_section(self, session_id: str, section_key: str, customization_request: str) -> str:
        """
        Customize a specific section of the script.
        
        Args:
            session_id: Session ID
            section_key: Key of the section to customize
            customization_request: User's customization request
            
        Returns:
            Customized section
        """
        session = self.active_sessions[session_id]
        generated_script = session.get("generated_script", "")
        generation_context = session.get("generation_context", {})
        
        if not generated_script:
            return "Es gibt noch kein generiertes Skript, das angepasst werden könnte."
        
        # Get section title
        section_info = TEMPLATE_STRUCTURE.get(section_key, {})
        section_title = section_info.get("title", section_key.replace("_", " ").title())
        
        # Extract the current section content
        section_pattern = re.compile(f"#{{{1,3}}}\\s*{re.escape(section_title)}.*?(?=#{{{1,3}}}|$)", re.DOTALL)
        match = section_pattern.search(generated_script)
        
        if not match:
            return f"Der Abschnitt '{section_title}' konnte im Skript nicht gefunden werden."
        
        current_section = match.group(0)
        
        # Get relevant context for this section
        query = f"{section_title} for {generation_context.get('session_context', {}).get('facility_type', 'medical facility')}"
        section_context = rag_controller.retrieve_context(query, generation_context.get("session_context", {}))
        formatted_context = rag_controller.format_retrieved_content_for_prompt(section_context)
        
        # Build customization prompt
        customization_prompt = prompt_builder.build_customization_prompt(
            base_content=current_section,
            customization_request=customization_request
        )
        
        # Add the context
        customization_prompt += f"\n\n# RELEVANT CONTEXT\n{formatted_context}"
        
        # Get system prompt
        system_prompt = prompt_builder.build_system_prompt()
        
        # Generate customized section
        try:
            customized_section = ollama_client.generate(
                prompt=customization_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            # Update the script with the customized section
            updated_script = re.sub(
                section_pattern,
                customized_section,
                generated_script
            )
            
            # Store the updated script
            session["generated_script"] = updated_script
            
            return f"Der Abschnitt '{section_title}' wurde erfolgreich angepasst. Möchten Sie das aktualisierte Skript sehen?"
            
        except Exception as e:
            system_logger.error(f"Error customizing script section for session {session_id}: {e}")
            return f"Bei der Anpassung des Abschnitts '{section_title}' ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut."

# Create a singleton instance
chatbot_engine = ChatbotEngine()