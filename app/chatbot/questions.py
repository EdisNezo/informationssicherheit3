"""
Questions module for the chatbot.
This module provides the strategic and contextual questions for collecting requirements.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path

CONTEXT_QUESTIONS = [
    {
        "id": "facility_type",
        "question": "In welcher medizinischen Einrichtung sollen die Schulungen umgesetzt werden?",
        "description": "Dies hilft uns, den spezifischen Kontext zu verstehen (z.B. Krankenhaus, Forschungseinrichtung, Arztpraxis)",
        "type": "text"
    },
    {
        "id": "focus_threats",
        "question": "Welche spezifischen Bedrohungen sind für Ihre Einrichtung besonders relevant?",
        "description": "Z.B. Phishing, Malware, Passwort-Sicherheit, Mobile Geräte, etc.",
        "type": "text"
    },
    {
        "id": "target_audience",
        "question": "Gibt es spezifische Personengruppen, die zu berücksichtigen sind?",
        "description": "Z.B. Pflegepersonal, Ärzte, Verwaltungsmitarbeiter, IT-Personal, Forschende",
        "type": "text"
    },
    {
        "id": "skill_level",
        "question": "Welche Vorkenntnisse haben die Teilnehmer im Bereich Informationssicherheit?",
        "description": "Grundlegend, Mittel, Fortgeschritten",
        "type": "text"
    },
    {
        "id": "duration",
        "question": "Wie lang darf die Schulung maximal sein (in Minuten)?",
        "description": "Kurze Schulungen fokussieren auf Kernpunkte, längere können detaillierter sein",
        "type": "number",
        "min": 15,
        "max": 180,
        "default": 60
    },
    {
        "id": "regulatory_requirements",
        "question": "Gibt es besondere regulatorische Anforderungen, die berücksichtigt werden müssen?",
        "description": "Z.B. DSGVO, spezifische Branchenrichtlinien, interne Compliance-Regeln",
        "type": "text"
    },
    {
        "id": "sensitive_data",
        "question": "Welche sensiblen Daten werden in Ihrer Einrichtung verarbeitet?",
        "description": "Z.B. Patientendaten, Forschungsdaten, Personaldaten",
        "type": "text"
    },
    {
        "id": "past_incidents",
        "question": "Gab es in der Vergangenheit bereits Sicherheitsvorfälle und welcher Art waren diese?",
        "description": "Frühere Vorfälle können wichtige Hinweise für die Schulung liefern",
        "type": "text"
    },
    {
        "id": "existing_measures",
        "question": "Welche technischen Sicherheitsmaßnahmen sind bereits implementiert?",
        "description": "Z.B. Firewalls, Antivirenlösungen, 2FA",
        "type": "text"
    },
    {
        "id": "work_routine",
        "question": "Wie sieht der typische Arbeitsalltag der Mitarbeiter in Bezug auf IT-Systeme aus?",
        "description": "Dies hilft uns, realistische Szenarien für die Schulung zu entwickeln",
        "type": "text"
    }
]

# Template questions based on the 7-step model
TEMPLATE_QUESTIONS = {
    "threat_awareness": {
        "question": "Bitte beschreiben Sie eine typische Arbeitssituation, in der die Sicherheitsbedrohung '{threat}' in Ihrer {facility} auftreten könnte.",
        "description": "Diese Information hilft uns, einen realistischen Kontext für die Schulung zu schaffen.",
        "example": "Ein neuer Arbeitstag startet und wie jeden Morgen überprüfen die Mitarbeiter zunächst ihr E-Mail-Postfach, da sie häufig wichtige E-Mails von Kollegen und externen Dienstleistern erhalten."
    },
    "threat_identification": {
        "question": "Welche spezifischen Merkmale oder Anzeichen könnten die Mitarbeiter auf die Bedrohung '{threat}' hinweisen?",
        "description": "Wir suchen nach konkreten Erkennungsmerkmalen, die Ihre Mitarbeiter wahrnehmen können.",
        "example": "Bei Phishing-E-Mails könnten dies sein: externe Absenderadressen, Aufforderungen zum Klicken auf Links, Dringlichkeitsformulierungen, etc."
    },
    "threat_impact": {
        "question": "Welche konkreten Auswirkungen könnte ein erfolgreicher '{threat}'-Angriff auf Ihre {facility} und Ihre Mitarbeiter haben?",
        "description": "Bitte berücksichtigen Sie finanzielle, rechtliche, betriebliche und Reputationsaspekte.",
        "example": "Die Angreifer könnten Daten stehlen, Systeme verschlüsseln und Lösegeld fordern oder im Namen der Mitarbeiter handeln."
    },
    "tactic_choice": {
        "question": "Welche Handlungsoptionen sollten Ihre Mitarbeiter haben, wenn sie mit einer potenziellen '{threat}'-Bedrohung konfrontiert werden?",
        "description": "Wir benötigen einen Überblick über die möglichen Reaktionen, einschließlich der zu bevorzugenden Option.",
        "example": "Plausibilität prüfen, Absender überprüfen, verdächtige Links nicht anklicken, IT-Helpdesk kontaktieren."
    },
    "tactic_justification": {
        "question": "Warum sind die von Ihnen genannten Maßnahmen gegen '{threat}' besonders wirksam und wichtig für Ihre {facility}?",
        "description": "Diese Begründung hilft Ihren Mitarbeitern, die Bedeutung der Sicherheitsmaßnahmen zu verstehen.",
        "example": "Durch Absenderprüfung kann festgestellt werden, ob die Person berechtigt ist, Informationen anzufordern. Das Nichtanklicken von Links verhindert Malware-Installationen."
    },
    "tactic_mastery": {
        "question": "Bitte beschreiben Sie schrittweise, wie Ihre Mitarbeiter die Schutzmaßnahmen gegen '{threat}' konkret umsetzen sollten.",
        "description": "Ein klarer, detaillierter Prozess hilft Ihren Mitarbeitern, die Maßnahmen korrekt anzuwenden.",
        "example": "1. Plausibilität prüfen, 2. Absenderadresse kontrollieren, 3. Bei Unsicherheit über alternativen Kanal nachfragen, 4. Verdächtige E-Mails melden."
    },
    "tactic_followup": {
        "question": "Welche Anschlusshandlungen sollten nach der Identifizierung oder dem Umgang mit einer '{threat}'-Bedrohung in Ihrer {facility} folgen?",
        "description": "Hierzu gehören Meldeverfahren, Dokumentation und weitere Schutzmaßnahmen.",
        "example": "Kollegen warnen, regelmäßig zu Informationssicherheit informieren, aufmerksam mit sensiblen Informationen umgehen."
    }
}

def get_strategic_questions() -> List[Dict[str, Any]]:
    """
    Get the list of strategic questions to ask during the requirements gathering phase.
    
    Returns:
        List of question dictionaries
    """
    return CONTEXT_QUESTIONS

def get_template_question(section_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a customized template question based on the context.
    
    Args:
        section_key: Key of the section (threat_awareness, threat_identification, etc.)
        context: Context information gathered from strategic questions
        
    Returns:
        Customized question dictionary
    """
    if section_key not in TEMPLATE_QUESTIONS:
        return {
            "question": f"Bitte beschreiben Sie Informationen für den Abschnitt {section_key}.",
            "description": "Wir benötigen Informationen für diesen Abschnitt des Schulungsskripts.",
            "example": ""
        }
    
    template = TEMPLATE_QUESTIONS[section_key].copy()
    
    # Get facility type and threat type from context
    facility_type = context.get("facility_type", "medizinischen Einrichtung")
    
    # Handle threats - might be a string or a list
    threat_type = context.get("focus_threats", "Informationssicherheitsbedrohung")
    if isinstance(threat_type, list) and threat_type:
        threat_type = threat_type[0]  # Use the first threat if it's a list
    
    # Customize the question with the specific context
    template["question"] = template["question"].format(
        facility=facility_type,
        threat=threat_type
    )
    
    return template

def load_template_from_json(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the template structure from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Template dictionary
    """
    # Default template if no file is provided or file can't be loaded
    default_template = {
        "template": "Informationssicherheits-E-Learning-Skript",
        "version": "1.0",
        "sections": [
            {"id": 1, "title": "Threat Awareness / Bedrohungsbewusstsein"},
            {"id": 2, "title": "Threat Identification / Bedrohungserkennung"},
            {"id": 3, "title": "Threat Impact Assessment / Bedrohungsausmaß"},
            {"id": 4, "title": "Tactic Choice / Taktische Maßnahmenauswahl"},
            {"id": 5, "title": "Tactic Justification / Maßnahmenrechtfertigung"},
            {"id": 6, "title": "Tactic Mastery / Maßnahmenbeherrschung"},
            {"id": 7, "title": "Tactic Check & Follow-Up / Anschlusshandlungen"}
        ]
    }
    
    if not filepath:
        return default_template
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            template = json.load(f)
        return template
    except Exception as e:
        print(f"Error loading template: {e}")
        return default_template

def get_section_keys() -> List[str]:
    """
    Get the list of section keys in the correct order.
    
    Returns:
        List of section keys
    """
    return [
        "threat_awareness",
        "threat_identification",
        "threat_impact",
        "tactic_choice",
        "tactic_justification",
        "tactic_mastery",
        "tactic_followup"
    ]