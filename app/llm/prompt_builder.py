"""
Prompt builder module for constructing effective prompts for the LLM.
This module provides functions for creating structured prompts for different scenarios.
"""

from typing import Dict, List, Any, Optional
import json

from app.config import TEMPLATE_STRUCTURE
from app.utils import system_logger

class PromptBuilder:
    """Builder for constructing prompts for the LLM."""
    
    def __init__(self):
        """Initialize the prompt builder."""
        system_logger.info("Initializing PromptBuilder")
    
    def build_system_prompt(self) -> str:
        """
        Build the system prompt for the script generation task.
        
        Returns:
            System prompt string
        """
        return """
        Du bist ein erfahrener Instructional Designer, spezialisiert auf Schulungen zur Informationssicherheit im medizinischen Kontext.
        Deine Aufgabe ist es, hochwertige, kompetenzbasierte Schulungsskripte zu erstellen, die einem spezifischen 7-Stufen-Template folgen.

        Du integrierst Elemente der Sozialen Lerntheorie (SLT) und der Schutzmotivationstheorie (PMT) in deine Skripte:
        - SLT: Einbeziehung von Szenarien, in denen Menschen durch Beobachtung des Verhaltens anderer und dessen Konsequenzen lernen
        - PMT: Einbeziehung realistischer Bedrohungsbeurteilungen und Wirksamkeitsinformationen zur Motivation von Schutzmaßnahmen

        Befolge diese Prinzipien:
        1. Verwende klare, präzise Sprache, die für medizinisches Fachpersonal geeignet ist
        2. Beziehe realistische Beispiele ein, die für medizinische Umgebungen relevant sind
        3. Sei spezifisch bei der Beschreibung von Bedrohungen, ihren Auswirkungen und Gegenmaßnahmen
        4. Vermeide Fachjargon, es sei denn, er ist notwendig, und erkläre ihn, wenn er verwendet wird
        5. Konzentriere dich auf praktische, umsetzbare Ratschläge
        6. Füge Schritt-für-Schritt-Anleitungen für komplexe Aufgaben ein
        7. Präsentiere den Inhalt in einer logischen Abfolge
        8. Achte darauf, dass das gesamte Skript zwischen 1500 und 2000 Wörtern umfasst

        Deine Skripte sollten ausschließlich auf Deutsch sein und reinen Text enthalten, ohne Bilder oder Multimediaelemente.
        """
    
    def build_chat_system_prompt(self) -> str:
        """
        Build the system prompt for the chatbot's conversation with users.
        
        Returns:
            System prompt string
        """
        return """
        You are an information security requirements analyst specializing in the medical sector. 
        Your job is to gather requirements from users to create customized security training materials.

        You should ask strategic, open-ended questions to understand:
        1. The type of medical facility (hospital, research lab, clinic, etc.)
        2. The target audience (doctors, nurses, researchers, admin staff, etc.)
        3. The desired length and depth of training
        4. Specific security concerns and threats that should be addressed
        5. Any regulatory requirements that must be covered

        Be friendly but professional. Ask one question at a time and wait for a response.
        Take note of all relevant information provided, even if not in direct response to a question.
        
        After gathering the required information, summarize what you've learned before proceeding.
        """
    
    def build_script_generation_prompt(self, 
                                     session_context: Dict[str, Any],
                                     retrieved_context: str) -> str:
        """
        Build the prompt for generating the complete script.
        
        Args:
            session_context: Session context with user requirements
            retrieved_context: Retrieved context from the RAG system
            
        Returns:
            Complete generation prompt
        """
        # Extract key variables from session context
        facility_type = session_context.get("facility_type", "medical facility")
        target_audience = session_context.get("target_audience", [])
        if isinstance(target_audience, list):
            audience_str = ", ".join(target_audience) if target_audience else "healthcare staff"
        else:
            audience_str = str(target_audience)
            
        duration = session_context.get("duration", 60)
        focus_threats = session_context.get("focus_threats", [])
        if isinstance(focus_threats, list):
            threats_str = ", ".join(focus_threats) if focus_threats else "general security threats"
        else:
            threats_str = str(focus_threats)
            
        skill_level = session_context.get("skill_level", "Mittel")
        
        # Create template structure
        template_structure = json.dumps(TEMPLATE_STRUCTURE, indent=2)
        
        # Escape all percent signs in the retrieved context to prevent format specifier errors
        safe_retrieved_context = retrieved_context.replace("%", "%%")
        
        prompt = f"""
        # TASK
        Erstelle ein umfassendes Schulungsskript zum Thema Informationssicherheit für {audience_str} in einer {facility_type}. Das Skript soll dem 7-Stufen-Template folgen und sich auf {threats_str} konzentrieren.

        # ANFORDERUNGEN
        - Das Schulungsskript muss auf Deutsch verfasst sein
        - Der Gesamtumfang soll zwischen 1500 und 2000 Wörtern liegen (wichtig!)
        - Verteile den Inhalt gleichmäßig auf alle sieben Abschnitte
        - Jeder Abschnitt sollte etwa 200-250 Wörter umfassen

        # KONTEXT
        - Einrichtungstyp: {facility_type}
        - Zielgruppe: {audience_str}
        - Schulungsdauer: {duration} Minuten
        - Schwerpunkt-Bedrohungen: {threats_str}
        - Technisches Niveau: {skill_level}
        - Zusätzlicher Kontext: {session_context.get("custom_scenarios", "")}
        - Regulatorische Anforderungen: {session_context.get("regulatory_requirements", "")}

        # TEMPLATE-STRUKTUR
        Das Skript muss dieser 7-stufigen kompetenzbasierten Vorlage folgen:
        ```json
        {template_structure}
        ```

        # ANWEISUNGEN
        1. Erstelle ein vollständiges Schulungsskript nach der oben genannten 7-Stufen-Vorlage
        2. Passe den Inhalt speziell für {audience_str} in einer {facility_type} an
        3. Konzentriere dich auf {threats_str} als primäre Sicherheitsbedrohungen
        4. Gestalte das Skript für eine {duration}-minütige Schulung
        5. Passe die technische Tiefe an das Niveau {skill_level} an
        6. Integriere realistische Beispiele und Szenarien aus dem medizinischen Kontext
        7. Baue Elemente der Sozialen Lerntheorie (Lernen durch Beobachtung) und der Schutzmotivationstheorie (realistische Bedrohungseinschätzung und Bewältigungsmaßnahmen) ein
        8. Verwende klare, präzise Sprache, die für medizinisches Fachpersonal geeignet ist
        9. Füge Schritt-für-Schritt-Anleitungen für Sicherheitsmaßnahmen ein
        10. Gestalte den Inhalt ansprechend und einprägsam
        11. Halte dich unbedingt an die Wortanzahl von 1500-2000 Wörtern insgesamt

        # AUSGABEFORMAT
        Liefere das vollständige Skript mit klaren Abschnittsüberschriften gemäß der 7-Stufen-Vorlage. Jeder Abschnitt sollte umfassend und detailliert sein, aber zusammen die Gesamtwortanzahl von 1500-2000 Wörtern nicht überschreiten oder unterschreiten.

        {safe_retrieved_context}

        # SKRIPT ANFANG
        """
        
        return prompt
    
    def build_section_generation_prompt(self, 
                                      section_key: str,
                                      session_context: Dict[str, Any],
                                      retrieved_context: str) -> str:
        """
        Build a prompt for generating a specific section of the script.
        
        Args:
            section_key: Key of the section to generate
            session_context: Session context with user requirements
            retrieved_context: Retrieved context from the RAG system
            
        Returns:
            Section generation prompt
        """
        # Get section information from the template structure
        section_info = TEMPLATE_STRUCTURE.get(section_key, {})
        section_title = section_info.get("title", section_key.replace("_", " ").title())
        section_description = section_info.get("description", "")
        section_questions = section_info.get("questions", [])
        
        # Extract key variables from session context
        facility_type = session_context.get("facility_type", "medical facility")
        target_audience = session_context.get("target_audience", [])
        if isinstance(target_audience, list):
            audience_str = ", ".join(target_audience) if target_audience else "healthcare staff"
        else:
            audience_str = str(target_audience)
            
        focus_threats = session_context.get("focus_threats", [])
        if isinstance(focus_threats, list):
            threats_str = ", ".join(focus_threats) if focus_threats else "general security threats"
        else:
            threats_str = str(focus_threats)
        
        # Escape all percent signs in the retrieved context to prevent format specifier errors
        safe_retrieved_context = retrieved_context.replace("%", "%%")
        
        # Build section-specific instructions
        section_instructions = ""
        if section_key == "threat_awareness":
            section_instructions = f"""
            For this section, describe the specific context in which security threats might occur for {audience_str} in a {facility_type}. Include:
            - Typical workplace scenarios where {threats_str} might be encountered
            - Day-to-day activities that could expose staff to security risks
            - Real-world examples relevant to healthcare environments
            - Integration of Social Learning Theory by showing how experienced staff might identify suspicious situations
            """
        elif section_key == "threat_identification":
            section_instructions = f"""
            For this section, clearly identify the specific indicators and characteristics of {threats_str}. Include:
            - Specific warning signs that staff should look for
            - Common patterns or techniques used in these attacks
            - Visual and content-based clues that indicate potential threats
            - Concrete examples tailored to the healthcare context
            - How to distinguish between legitimate and suspicious communications
            """
        elif section_key == "threat_impact":
            section_instructions = f"""
            For this section, describe the potential consequences of {threats_str} in detail. Include:
            - Direct impacts on patient care and safety
            - Potential data breaches and confidentiality violations
            - Regulatory and compliance implications specific to healthcare
            - Financial and reputational damage to the organization
            - Personal consequences for staff members
            - Integration of Protection Motivation Theory by presenting realistic threat scenarios
            """
        elif section_key == "tactic_choice":
            section_instructions = f"""
            For this section, outline the various options staff have when confronted with {threats_str}. Include:
            - Clear decision frameworks for different threat scenarios
            - Immediate actions that can be taken to minimize risk
            - Options for reporting or escalating security concerns
            - Guidance on when to contact IT security versus handling independently
            - Recommendations for the safest course of action in different contexts
            """
        elif section_key == "tactic_justification":
            section_instructions = f"""
            For this section, explain why the recommended actions are effective against {threats_str}. Include:
            - Evidence-based reasoning for security recommendations
            - How the recommended tactics mitigate specific risks
            - Why certain responses are preferred over alternatives
            - Integration of Protection Motivation Theory by emphasizing response efficacy
            - Real-world examples where these tactics have prevented security incidents
            """
        elif section_key == "tactic_mastery":
            section_instructions = f"""
            For this section, provide detailed, step-by-step instructions for implementing security measures against {threats_str}. Include:
            - Precise procedural steps with clear numbering
            - Technical instructions written at an appropriate level for {audience_str}
            - Common pitfalls or mistakes to avoid
            - Screenshots or descriptions of relevant user interfaces
            - Integration of Social Learning Theory by describing model behavior
            """
        elif section_key == "tactic_followup":
            section_instructions = f"""
            For this section, describe follow-up actions and ongoing practices after a security event or implementation of security measures. Include:
            - Reporting procedures specific to the {facility_type}
            - Documentation requirements for security incidents
            - Ongoing monitoring and verification steps
            - How to share learnings with colleagues
            - Integration with existing security protocols and practices
            """
        
        # Build the complete prompt
        questions_str = "\n".join([f"- {q}" for q in section_questions])
        
        prompt = f"""
        # SECTION GENERATION TASK
        Create the "{section_title}" section for an information security training script focused on {threats_str}.

        # SECTION DESCRIPTION
        {section_description}

        # KEY QUESTIONS TO ADDRESS
        {questions_str}

        # SECTION-SPECIFIC INSTRUCTIONS
        {section_instructions}

        # CONTEXT
        - Target Audience: {audience_str}
        - Facility Type: {facility_type}
        - Focus Threats: {threats_str}
        
        {safe_retrieved_context}

        # WRITE THE COMPLETE SECTION CONTENT BELOW
        ## {section_title}
        """
        
        return prompt
    
    def build_summary_prompt(self, session_context: Dict[str, Any], script_sections: Dict[str, str]) -> str:
        """
        Build a prompt for generating a summary of the script.
        
        Args:
            session_context: Session context with user requirements
            script_sections: Dictionary of generated script sections
            
        Returns:
            Summary generation prompt
        """
        # Extract key variables from session context
        facility_type = session_context.get("facility_type", "medical facility")
        target_audience = session_context.get("target_audience", [])
        if isinstance(target_audience, list):
            audience_str = ", ".join(target_audience) if target_audience else "healthcare staff"
        else:
            audience_str = str(target_audience)
            
        duration = session_context.get("duration", 60)
        focus_threats = session_context.get("focus_threats", [])
        if isinstance(focus_threats, list):
            threats_str = ", ".join(focus_threats) if focus_threats else "general security threats"
        else:
            threats_str = str(focus_threats)
        
        # Build the summary prompt
        prompt = f"""
        # SUMMARY GENERATION TASK
        Create a brief executive summary of the information security training script on {threats_str} for {audience_str} in a {facility_type}.

        # SCRIPT SECTIONS
        The script contains the following sections:
        
        """
        
        # Add section titles and first few lines of content
        for section_key, section_content in script_sections.items():
            section_info = TEMPLATE_STRUCTURE.get(section_key, {})
            section_title = section_info.get("title", section_key.replace("_", " ").title())
            
            # Extract first 100 characters as preview
            preview = section_content[:100] + "..." if len(section_content) > 100 else section_content
            
            prompt += f"## {section_title}\n{preview}\n\n"
        
        prompt += f"""
        # INSTRUCTIONS
        Create an executive summary (200-300 words) that:
        1. Highlights the key security threats addressed ({threats_str})
        2. Summarizes the main learning objectives
        3. Describes how the training is tailored to {audience_str} in a {facility_type}
        4. Mentions the training duration ({duration} minutes)
        5. Emphasizes the practical security skills covered

        # EXECUTIVE SUMMARY
        """
        
        return prompt
    
    def build_customization_prompt(self, base_content: str, customization_request: str) -> str:
        """
        Build a prompt for customizing existing content based on user feedback.
        
        Args:
            base_content: Original content to customize
            customization_request: User's request for changes
            
        Returns:
            Customization prompt
        """
        # Escape percent signs to prevent format issues
        safe_base_content = base_content.replace("%", "%%")
        safe_customization_request = customization_request.replace("%", "%%")
        
        prompt = f"""
        # CONTENT CUSTOMIZATION TASK
        Modify the following training script content based on the customization request.

        # ORIGINAL CONTENT
        {safe_base_content}

        # CUSTOMIZATION REQUEST
        {safe_customization_request}

        # INSTRUCTIONS
        1. Carefully review the original content and the customization request
        2. Make targeted changes to address the specific requests
        3. Maintain the overall structure, tone, and quality of the original content
        4. Focus only on modifying aspects mentioned in the customization request
        5. If the request is unclear, make minimal changes that best align with the apparent intent

        # MODIFIED CONTENT
        """
        
        return prompt
    
    def build_hallucination_check_prompt(self, 
                                       generated_content: str, 
                                       retrieved_context: str) -> str:
        """
        Build a prompt for checking generated content for potential hallucinations.
        
        Args:
            generated_content: The content to check
            retrieved_context: The retrieved context used for generation
            
        Returns:
            Hallucination check prompt
        """
        # Escape percent signs to prevent format issues
        safe_generated_content = generated_content.replace("%", "%%")
        safe_retrieved_context = retrieved_context.replace("%", "%%")
        
        prompt = f"""
        # HALLUCINATION DETECTION TASK
        Carefully analyze the generated content and identify any statements that might be hallucinations (facts or claims that are not supported by the retrieved context).

        # GENERATED CONTENT
        {safe_generated_content}

        # RETRIEVED CONTEXT (GROUND TRUTH)
        {safe_retrieved_context}

        # INSTRUCTIONS
        1. Compare the generated content against the retrieved context
        2. Identify any statements in the generated content that:
           - Contradict information in the retrieved context
           - Make specific factual claims not supported by the retrieved context
           - Introduce terminology, procedures, or concepts not present in the retrieved context
        3. Ignore stylistic differences and focus only on factual accuracy
        4. For each potential hallucination, provide:
           - The exact quote from the generated content
           - Why it appears to be a hallucination
           - A suggested correction (if possible)

        # OUTPUT FORMAT
        Provide your analysis in the following JSON format:
        {{
          "has_hallucinations": true/false,
          "hallucinations": [
            {{
              "text": "quoted text from generated content",
              "reason": "explanation of why this is a hallucination",
              "correction": "suggested correction"
            }},
            ...
          ]
        }}

        If no hallucinations are found, return:
        {{
          "has_hallucinations": false,
          "hallucinations": []
        }}

        # ANALYSIS
        """
        
        return prompt

# Create a singleton instance
prompt_builder = PromptBuilder()