"""
Chatbot engine module that manages the conversation with the user.
This module coordinates the question-answering process and maintains conversation state.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import json
import re
from datetime import datetime
import traceback

from app.utils import system_logger, time_operation, generate_session_id, log_chat_message
from app.llm.ollama_client import ollama_client
from app.llm.prompt_builder import prompt_builder
from app.rag.controller import rag_controller
from app.chatbot.dialogue import dialogue_manager
from app.chatbot.questions import get_strategic_questions, get_section_keys
from app.config import TEMPLATE_STRUCTURE, HALLUCINATION_MANAGEMENT

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
            "stage": "introduction",
            "messages": [],
            "generated_script": None
        }
        
        # Initialize dialogue state
        dialogue_manager.initialize_dialogue(session_id)
        
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

        Um ein maßgeschneidertes Schulungsskript zu erstellen, werde ich Ihnen eine Reihe von Fragen stellen:
        
        1. Zunächst einige Fragen zum Kontext Ihrer medizinischen Einrichtung, um Ihre Anforderungen zu verstehen
        2. Danach spezifische Fragen zu den sieben Kompetenzbereichen der Informationssicherheit

        Basierend auf Ihren Antworten werde ich ein strukturiertes Schulungsskript erstellen, das Sie für E-Learning-Zwecke verwenden können.

        Lassen Sie uns beginnen!
        """
        
        # Add this message to the session history
        if session_id in self.active_sessions:
            self._add_message_to_session(session_id, "assistant", introduction)
        
        # Advance the dialogue to the next stage
        dialogue_manager.advance_dialogue(session_id)
        
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
        dialogue_state = dialogue_manager.get_dialogue_state(session_id)
        
        if not dialogue_state:
            return "Es ist ein Fehler mit Ihrer Sitzung aufgetreten. Bitte starten Sie eine neue Sitzung."
        
        current_stage = dialogue_state["current_stage"]
        
        # Process the message based on the current stage
        if current_stage == "introduction":
            # Move to context questions stage
            dialogue_manager.advance_dialogue(session_id)
            response = self._get_next_question(session_id)
            
        elif current_stage == "context_questions" or current_stage == "template_questions":
            # Get the current question
            current_question = dialogue_manager.get_next_question(session_id)
            
            if current_question:
                # Process the response to the current question
                dialogue_manager.process_response(session_id, current_question["id"], message)
                
                # Advance to the next question
                dialogue_manager.advance_dialogue(session_id)
                
                # Get the next question
                response = self._get_next_question(session_id)
            else:
                # If no more questions, move to summary
                response = self._generate_summary(session_id)
        
        elif current_stage == "summary":
            # Process the summary response
            if "generieren" in message.lower() or "erstellen" in message.lower() or "ja" in message.lower():
                # Generate the script
                response = self._generate_script(session_id)
            else:
                # Ask if they want to make changes
                response = """
                Möchten Sie Änderungen an den gesammelten Informationen vornehmen, oder soll ich das Skript basierend auf den aktuellen Informationen generieren?
                """
        
        elif current_stage == "complete":
            # If the dialogue is complete, check if they want to see the script
            if "zeigen" in message.lower() or "anzeigen" in message.lower() or "sehen" in message.lower():
                # Show the generated script
                response = self.get_generated_script(session_id)
            elif "neu" in message.lower() or "starten" in message.lower():
                # Create a new session
                dialogue_manager.initialize_dialogue(session_id)
                session["stage"] = "introduction"
                response = self.get_introduction_message(session_id)
            else:
                # Default response
                response = """
                Das Skript wurde erfolgreich generiert. Sie können es jetzt einsehen oder eine neue Sitzung starten.
                
                - Geben Sie "Skript anzeigen" ein, um das vollständige Skript zu sehen.
                - Geben Sie "Neu starten" ein, um mit einem neuen Skript zu beginnen.
                """
        
        else:
            # Handle unexpected stage
            system_logger.error(f"Unexpected stage '{current_stage}' for session {session_id}")
            response = "Es ist ein Fehler aufgetreten. Bitte starten Sie eine neue Sitzung."
        
        # Add response to history
        self._add_message_to_session(session_id, "assistant", response)
        
        # Update session stage based on dialogue state
        session["stage"] = dialogue_manager.get_dialogue_state(session_id)["current_stage"]
        
        return response
    
    def _get_next_question(self, session_id: str) -> str:
        """
        Get the next question to ask the user.
        
        Args:
            session_id: Session ID
            
        Returns:
            Question text or summary if no more questions
        """
        # Get the next question from the dialogue manager
        question = dialogue_manager.get_next_question(session_id)
        
        if not question:
            # If no more questions, generate a summary
            return self._generate_summary(session_id)
        
        # Format the question
        question_text = question["question"]
        description = question.get("description", "")
        
        # Add an example if available
        example = question.get("example", "")
        if example:
            example_text = f"\n\n*Beispiel:* {example}"
        else:
            example_text = ""
        
        # Create the formatted question
        formatted_question = f"""
        {question_text}
        
        {description}{example_text}
        """
        
        return formatted_question
    
    def _generate_summary(self, session_id: str) -> str:
        """
        Generate a summary of the collected information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Summary text
        """
        # Get the dialogue summary
        summary = dialogue_manager.get_dialogue_summary(session_id)
        
        # Format the summary
        summary_parts = ["## Zusammenfassung Ihrer Antworten\n"]
        
        for question, response in summary["responses"].items():
            summary_parts.append(f"**Frage:** {question}\n")
            summary_parts.append(f"**Antwort:** {response}\n")
        
        summary_parts.append("\n## Nächste Schritte\n")
        summary_parts.append("Basierend auf Ihren Antworten kann ich jetzt ein maßgeschneidertes Schulungsskript erstellen. Das Skript wird zwischen 1500 und 2000 Wörtern umfassen und auf Deutsch verfasst sein. Möchten Sie fortfahren und das Skript generieren?")
        
        return "\n".join(summary_parts)
    
    @time_operation
    def _generate_script(self, session_id: str) -> str:
        """
        Generate the complete training script.
        
        Args:
            session_id: Session ID
            
        Returns:
            Message about script generation
        """
        session = self.active_sessions[session_id]
        
        # Get the script generation context
        script_context = dialogue_manager.get_script_generation_context(session_id)
        
        # Log the generation request
        system_logger.info(f"Generating script for session {session_id} with context: {json.dumps(script_context)}")
        
        try:
            # Retrieve relevant context from the RAG system
            # Create a query based on the script context
            facility_type = script_context.get("facility_type", "medical facility")
            focus_threats = script_context.get("focus_threats", "security threats")
            target_audience = script_context.get("target_audience", "healthcare staff")
            
            # Build the query
            query = f"Security training for {facility_type} focused on {focus_threats} for {target_audience}"
            
            # Retrieve strategic context
            strategic_context = rag_controller.retrieve_context(query, script_context)
            
            # Get template examples
            main_threat = focus_threats.split(",")[0].strip() if isinstance(focus_threats, str) else "phishing"
            template_examples = rag_controller.retrieve_template_examples("seven_step", main_threat)
            
            # Get detailed threat info
            threats = [main_threat]
            threat_info = rag_controller.retrieve_threat_info(threats)
            
            # Combine all retrieved information
            combined_context = rag_controller.combine_retrieval_results(
                strategic_context=strategic_context,
                template_examples=template_examples,
                threat_info=threat_info
            )
            
            # Format the retrieved content for the prompt
            formatted_context = rag_controller.format_retrieved_content_for_prompt(combined_context)
            
            # Build the script sections based on collected information
            script_sections = {}
            
            # Process each section
            for section_key in get_section_keys():
                section_id = f"template_{section_key}"
                
                if section_id in script_context:
                    # Use the user's response for this section
                    content = script_context[section_id]
                    
                    # Get the section title
                    section_info = TEMPLATE_STRUCTURE.get(section_key, {})
                    title = section_info.get("title", section_key.replace("_", " ").title())
                    
                    script_sections[section_key] = {
                        "title": title,
                        "content": content
                    }
            
            # Now we need to build a complete script
            script_content = self._format_script_content(
                script_sections=script_sections,
                script_context=script_context
            )
            
            # Store the generated script
            session["generated_script"] = script_content
            session["script_context"] = script_context
            
            # Update dialogue stage to complete
            dialogue_state = dialogue_manager.get_dialogue_state(session_id)
            dialogue_state["current_stage"] = "complete"
            
            # Format a response message about successful generation
            response = """
            ## Skript erfolgreich erstellt!
            
            Ich habe das Schulungsskript basierend auf Ihren Antworten erstellt. Das Skript folgt dem 7-Stufen-Template und wurde speziell für Ihre Anforderungen angepasst.
            
            Das Skript umfasst zwischen 1500 und 2000 Wörtern und ist vollständig auf Deutsch verfasst.
            
            Sie können nun folgende Aktionen durchführen:
            
            - **Skript anzeigen:** Um das vollständige generierte Skript zu sehen
            - **Neu starten:** Um mit einem neuen Skript zu beginnen
            """
            
            return response
            
        except Exception as e:
            system_logger.error(f"Error generating script for session {session_id}: {e}")
            system_logger.error(traceback.format_exc())
            
            # Update stage to indicate failure
            session["stage"] = "summary"
            
            return "Bei der Erstellung des Skripts ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut oder passen Sie Ihre Anforderungen an."
    
    def _format_script_content(self, script_sections: Dict[str, Dict[str, str]], script_context: Dict[str, Any]) -> str:
        """
        Format the script sections into a complete script.
        
        Args:
            script_sections: Dictionary of script sections
            script_context: Context information for the script
            
        Returns:
            Formatted script content
        """
        # Get context variables
        facility_type = script_context.get("facility_type", "medizinische Einrichtung")
        threat_types = script_context.get("focus_threats", "Informationssicherheitsbedrohungen")
        target_audience = script_context.get("target_audience", "Mitarbeiter im Gesundheitswesen")
        
        # Create title
        script_title = f"Schulungsskript: {threat_types} für {target_audience} in {facility_type}"
        
        # Start building the script
        script_parts = [f"# {script_title}\n"]
        
        # Add introduction
        script_parts.append(f"""
        ## Einleitung
        
        Willkommen zum Trainingsmodul zum Thema {threat_types}. In diesem Modul lernen Sie, wie Mitarbeiter in {facility_type} Sicherheitsbedrohungen erkennen und damit umgehen können.
        """)
        
        # Add each section
        for section_key in get_section_keys():
            if section_key in script_sections:
                section = script_sections[section_key]
                title = section.get("title", "")
                content = section.get("content", "")
                
                script_parts.append(f"\n## {title}\n")
                script_parts.append(content)
        
        # Add conclusion
        script_parts.append(f"""
        ## Abschluss
        
        Herzlichen Glückwunsch! Sie haben dieses Trainingsmodul zum Thema {threat_types} abgeschlossen.
        
        Durch die Anwendung des erlernten Wissens tragen Sie dazu bei, {facility_type} sicherer zu machen und sensible Daten zu schützen.
        """)
        
        # Add metadata
        script_parts.append(f"""
        ## Metadaten
        
        - **Erstellungsdatum:** {datetime.now().strftime("%d.%m.%Y")}
        - **Zielgruppe:** {target_audience}
        - **Einrichtung:** {facility_type}
        - **Schwerpunkt:** {threat_types}
        - **Empfohlene Schulungsdauer:** {script_context.get("duration", "60")} Minuten
        - **Wortanzahl:** Zwischen 1500 und 2000 Wörtern
        """)
        
        return "\n".join(script_parts)
    
    def get_generated_script(self, session_id: str) -> str:
        """
        Get the generated script for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Generated script or error message
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return "Keine aktive Sitzung gefunden. Bitte starten Sie eine neue Sitzung."
            
        generated_script = session.get("generated_script")
        if not generated_script:
            return "Es wurde noch kein Skript generiert. Bitte durchlaufen Sie den Frageprozess, um ein Skript zu erstellen."
        
        return f"## Generiertes Schulungsskript\n\n{generated_script}"

# Create a singleton instance
chatbot_engine = ChatbotEngine()