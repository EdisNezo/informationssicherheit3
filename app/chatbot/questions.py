"""
Questions module for the chatbot.
This module provides the strategic and contextual questions for collecting requirements.
"""

from typing import List, Dict, Any, Optional
from app.config import STRATEGIC_QUESTIONS

def get_strategic_questions() -> List[Dict[str, Any]]:
    """
    Get the list of strategic questions to ask during the requirements gathering phase.
    
    Returns:
        List of question dictionaries
    """
    return STRATEGIC_QUESTIONS

def get_contextual_questions(facility_type: str, target_audience: List[str], focus_threats: List[str]) -> List[Dict[str, Any]]:
    """
    Get contextual questions based on the facility type, target audience, and focus threats.
    
    Args:
        facility_type: Type of medical facility
        target_audience: Target audience groups
        focus_threats: Focus threat types
        
    Returns:
        List of contextual question dictionaries
    """
    contextual_questions = []
    
    # Facility-specific questions
    if "Krankenhaus" in facility_type or "Klinik" in facility_type:
        contextual_questions.append({
            "id": "hospital_specific",
            "question": "Gibt es in Ihrem Krankenhaus/Ihrer Klinik spezifische Bereiche mit besonderem Schutzbedarf (z.B. Intensivstation, OP-Bereich)?",
            "description": "Diese Information hilft uns, die Schulung auf besonders sensible Bereiche auszurichten",
            "type": "text"
        })
        
        contextual_questions.append({
            "id": "patient_data_systems",
            "question": "Welche Patientendatensysteme werden in Ihrer Einrichtung verwendet?",
            "description": "Die Nennung konkreter Systeme ermöglicht uns, spezifische Sicherheitsmaßnahmen in die Schulung zu integrieren",
            "type": "text"
        })
        
    elif "Forschung" in facility_type or "Labor" in facility_type:
        contextual_questions.append({
            "id": "research_data",
            "question": "Welche Arten von Forschungsdaten werden in Ihrer Einrichtung verarbeitet?",
            "description": "Diese Information hilft uns, die Schulung auf den Schutz sensibler Forschungsdaten auszurichten",
            "type": "text"
        })
        
        contextual_questions.append({
            "id": "international_collaboration",
            "question": "Arbeiten Sie mit internationalen Forschungspartnern zusammen?",
            "description": "Internationale Zusammenarbeit bringt zusätzliche Sicherheitsaspekte mit sich",
            "type": "boolean"
        })
        
    elif "Praxis" in facility_type or "Arzt" in facility_type:
        contextual_questions.append({
            "id": "practice_size",
            "question": "Wie viele Mitarbeiter sind in Ihrer Praxis tätig?",
            "description": "Die Größe der Praxis beeinflusst die Organisation der Sicherheitsmaßnahmen",
            "type": "number"
        })
        
        contextual_questions.append({
            "id": "electronic_prescription",
            "question": "Nutzen Sie elektronische Rezepte oder andere digitale Verordnungssysteme?",
            "description": "Diese Systeme bringen spezifische Sicherheitsanforderungen mit sich",
            "type": "boolean"
        })
    
    # Audience-specific questions
    if "Ärzte" in target_audience:
        contextual_questions.append({
            "id": "doctor_workflow",
            "question": "In welchen typischen Arbeitssituationen nutzen Ärzte in Ihrer Einrichtung IT-Systeme?",
            "description": "Dies hilft uns, die Schulung in den konkreten Arbeitsalltag zu integrieren",
            "type": "text"
        })
        
    if "Pflegepersonal" in target_audience:
        contextual_questions.append({
            "id": "nurse_devices",
            "question": "Welche mobilen Geräte nutzt das Pflegepersonal bei der täglichen Arbeit?",
            "description": "Mobile Geräte haben besondere Sicherheitsanforderungen",
            "type": "text"
        })
        
    if "Verwaltungsmitarbeiter" in target_audience:
        contextual_questions.append({
            "id": "admin_access",
            "question": "Welche sensiblen Systeme und Daten werden von Verwaltungsmitarbeitern verwaltet?",
            "description": "Dies hilft uns, die spezifischen Bedrohungen für Verwaltungspersonal zu adressieren",
            "type": "text"
        })
        
    if "IT-Personal" in target_audience:
        contextual_questions.append({
            "id": "it_infrastructure",
            "question": "Wie ist Ihre IT-Infrastruktur aufgebaut (On-Premise, Cloud, Hybrid)?",
            "description": "Die Infrastruktur bestimmt die relevanten Sicherheitsmaßnahmen",
            "type": "text"
        })
    
    # Threat-specific questions
    if "Phishing" in focus_threats:
        contextual_questions.append({
            "id": "phishing_incidents",
            "question": "Gab es in der Vergangenheit Phishing-Vorfälle in Ihrer Einrichtung?",
            "description": "Frühere Vorfälle können hilfreiche Beispiele für die Schulung liefern",
            "type": "text"
        })
        
    if "Malware" in focus_threats:
        contextual_questions.append({
            "id": "removable_media",
            "question": "Werden in Ihrer Einrichtung regelmäßig externe Speichermedien verwendet?",
            "description": "Externe Speichermedien sind ein häufiger Übertragungsweg für Malware",
            "type": "boolean"
        })
        
    if "Passwort-Sicherheit" in focus_threats:
        contextual_questions.append({
            "id": "password_policy",
            "question": "Gibt es in Ihrer Einrichtung eine definierte Passwort-Richtlinie?",
            "description": "Bestehende Richtlinien sollten in die Schulung integriert werden",
            "type": "text"
        })
        
    if "Datendiebstahl" in focus_threats:
        contextual_questions.append({
            "id": "data_classification",
            "question": "Gibt es in Ihrer Einrichtung ein System zur Klassifizierung von Daten nach Schutzbedarf?",
            "description": "Ein Klassifizierungssystem hilft bei der Priorisierung von Schutzmaßnahmen",
            "type": "text"
        })
        
    if "Mobile Geräte" in focus_threats:
        contextual_questions.append({
            "id": "byod_policy",
            "question": "Erlauben Sie die Nutzung privater Geräte für dienstliche Zwecke (BYOD)?",
            "description": "BYOD-Richtlinien beeinflussen die Sicherheitsanforderungen für mobile Geräte",
            "type": "boolean"
        })
    
    # General additional questions
    contextual_questions.append({
        "id": "previous_training",
        "question": "Gab es bereits frühere Schulungen zum Thema Informationssicherheit in Ihrer Einrichtung?",
        "description": "Dies hilft uns, die neue Schulung optimal auf den bestehenden Wissensstand abzustimmen",
        "type": "text"
    })
    
    contextual_questions.append({
        "id": "specific_examples",
        "question": "Haben Sie spezifische Beispiele oder Szenarien, die in der Schulung berücksichtigt werden sollten?",
        "description": "Konkrete Beispiele aus dem Arbeitsalltag machen die Schulung praxisnäher",
        "type": "text"
    })
    
    return contextual_questions

def get_clarification_questions(missing_fields: List[str]) -> List[Dict[str, Any]]:
    """
    Get clarification questions for missing information.
    
    Args:
        missing_fields: List of fields with missing information
        
    Returns:
        List of clarification question dictionaries
    """
    clarification_questions = []
    
    for field in missing_fields:
        if field == "facility_type":
            clarification_questions.append({
                "id": "clarify_facility",
                "question": "Könnten Sie bitte die Art Ihrer medizinischen Einrichtung genauer beschreiben?",
                "description": "Zum Beispiel: Krankenhaus, Forschungslabor, Arztpraxis, etc.",
                "type": "text"
            })
        
        elif field == "target_audience":
            clarification_questions.append({
                "id": "clarify_audience",
                "question": "Für welche Personengruppen soll die Schulung erstellt werden?",
                "description": "Zum Beispiel: Ärzte, Pflegepersonal, Verwaltung, IT-Personal, etc.",
                "type": "text"
            })
        
        elif field == "duration":
            clarification_questions.append({
                "id": "clarify_duration",
                "question": "Wie lang soll die Schulung maximal sein (in Minuten)?",
                "description": "Eine typische Schulung dauert zwischen 30 und 90 Minuten",
                "type": "number"
            })
        
        elif field == "focus_threats":
            clarification_questions.append({
                "id": "clarify_threats",
                "question": "Auf welche Sicherheitsbedrohungen soll die Schulung besonders eingehen?",
                "description": "Zum Beispiel: Phishing, Malware, Passwort-Sicherheit, etc.",
                "type": "text"
            })
        
        elif field == "skill_level":
            clarification_questions.append({
                "id": "clarify_skill",
                "question": "Wie schätzen Sie das durchschnittliche IT-Sicherheitswissen der Zielgruppe ein?",
                "description": "Grundlegend, Mittel oder Fortgeschritten",
                "type": "text"
            })
    
    return clarification_questions

def get_followup_questions() -> List[Dict[str, Any]]:
    """
    Get follow-up questions for after script generation.
    
    Returns:
        List of follow-up question dictionaries
    """
    return [
        {
            "id": "satisfaction",
            "question": "Wie zufrieden sind Sie mit dem generierten Schulungsskript?",
            "description": "Bitte bewerten Sie auf einer Skala von 1 (gar nicht zufrieden) bis 5 (sehr zufrieden)",
            "type": "rating",
            "min": 1,
            "max": 5
        },
        {
            "id": "improvements",
            "question": "Gibt es Bereiche, die noch verbessert werden sollten?",
            "description": "Ihre Rückmeldung hilft uns, das Skript optimal anzupassen",
            "type": "text"
        },
        {
            "id": "additional_topics",
            "question": "Gibt es weitere Themen, die im Skript behandelt werden sollten?",
            "description": "Wir können das Skript um zusätzliche Themen erweitern",
            "type": "text"
        },
        {
            "id": "implementability",
            "question": "Wie gut lässt sich das Skript in Ihrer Einrichtung umsetzen?",
            "description": "Sind die vorgeschlagenen Maßnahmen in Ihrem Kontext realistisch?",
            "type": "text"
        }
    ]