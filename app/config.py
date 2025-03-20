"""
Configuration management for the Security Script Generator application.
This module loads environment variables and provides configuration settings for all components.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
VECTORS_DIR = DATA_DIR / "vectors"
LOGS_DIR = DATA_DIR / "logs"

# Create directories if they don't exist
for directory in [DOCS_DIR, VECTORS_DIR, LOGS_DIR, 
                 LOGS_DIR / "chat_logs", 
                 LOGS_DIR / "generation_logs",
                 LOGS_DIR / "system_logs"]:
    directory.mkdir(parents=True, exist_ok=True)

# LLM Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # Default to mistral

# Vector Database Configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")  # Options: chroma, faiss, milvus
VECTOR_DB_PATH = VECTORS_DIR / "index"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CHAT_LOG_PATH = LOGS_DIR / "chat_logs"
GENERATION_LOG_PATH = LOGS_DIR / "generation_logs"
SYSTEM_LOG_PATH = LOGS_DIR / "system_logs"

# Template Configuration
TEMPLATE_STRUCTURE = {
    "threat_awareness": {
        "title": "Threat Awareness / Bedrohungsbewusstsein",
        "description": "Beschreibung des Kontextes, in dem Bedrohungen auftreten",
        "questions": [
            "Was ist der Kontext?",
            "Was ist die Ausgangssituation?",
            "In welchen Szenarien tritt die Gefahr auf?"
        ]
    },
    "threat_identification": {
        "title": "Threat Identification / Bedrohungserkennung",
        "description": "Aufzeigen, welche Indikatoren auf eine Bedrohung hinweisen",
        "questions": [
            "Was ist oder worin besteht die Gefahr?",
            "Welche Merkmale gibt es?",
            "Wie erkenne ich diese?"
        ]
    },
    "threat_impact": {
        "title": "Threat Impact Assessment / Bedrohungsausmaß",
        "description": "Konkrete Darstellung der möglichen Folgen eines Angriffs",
        "questions": [
            "Was sind die Konsequenzen, die aus der Bedrohung entstehen können?",
            "Welche persönlichen und organisatorischen Auswirkungen könnten eintreten?"
        ]
    },
    "tactic_choice": {
        "title": "Tactic Choice / Taktische Maßnahmenauswahl",
        "description": "Übersicht möglicher Handlungsoptionen bei Erkennen einer Bedrohung",
        "questions": [
            "Was sind die Handlungsoptionen zwischen denen grundsätzlich gewählt werden kann?",
            "Welche sollte gewählt werden?"
        ]
    },
    "tactic_justification": {
        "title": "Tactic Justification / Maßnahmenrechtfertigung",
        "description": "Begründung, warum die gewählte Maßnahme besonders effektiv ist",
        "questions": [
            "Warum genau ist die Maßnahme/Handlungsoption besser als andere?"
        ]
    },
    "tactic_mastery": {
        "title": "Tactic Mastery / Maßnahmenbeherrschung",
        "description": "Detaillierte Schritt-für-Schritt-Anleitung zur Umsetzung der gewählten Maßnahme",
        "questions": [
            "Wie muss konkret vorgegangen werden, um die gewählte Handlung umzusetzen?",
            "Was sind die einzelnen Schritte, auf die geachtet werden muss?"
        ]
    },
    "tactic_followup": {
        "title": "Tactic Check & Follow-Up / Anschlusshandlungen",
        "description": "Festlegung von Nachkontrollen und weiteren Maßnahmen",
        "questions": [
            "Was sind konkrete Anschlusshandlungen, die nach der Ausführung noch getätigt werden müssen?",
            "Wer bleibt über was auf dem Laufenden?"
        ]
    }
}

# Strategic questions for the initial conversation
STRATEGIC_QUESTIONS = [
    {
        "id": "facility_type",
        "question": "In welcher medizinischen Einrichtung sollen die Schulungen umgesetzt werden?",
        "description": "Dies hilft uns, den spezifischen Kontext zu verstehen (z.B. Krankenhaus, Forschungseinrichtung, Arztpraxis)",
        "type": "text"
    },
    {
        "id": "target_audience",
        "question": "Welche Personengruppen sollen geschult werden?",
        "description": "Z.B. Pflegepersonal, Ärzte, Verwaltungsmitarbeiter, IT-Personal, Forschende",
        "type": "multi-select",
        "options": ["Pflegepersonal", "Ärzte", "Verwaltungsmitarbeiter", "IT-Personal", "Forschende", "Sonstige"]
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
        "id": "focus_threats",
        "question": "Auf welche Bedrohungen soll besonders eingegangen werden?",
        "description": "Wählen Sie die Bedrohungsszenarien, die für Ihre Einrichtung besonders relevant sind",
        "type": "multi-select",
        "options": ["Phishing", "Malware", "Social Engineering", "Passwort-Sicherheit", "Datendiebstahl", "Mobile Geräte", "Sonstige"]
    },
    {
        "id": "skill_level",
        "question": "Wie schätzen Sie das durchschnittliche IT-Sicherheitswissen der Zielgruppe ein?",
        "description": "Dies hilft uns, den Detailgrad und die Komplexität der Schulung anzupassen",
        "type": "single-select",
        "options": ["Grundlegend", "Mittel", "Fortgeschritten"]
    },
    {
        "id": "regulatory_requirements",
        "question": "Welche regulatorischen Anforderungen sind zu berücksichtigen?",
        "description": "Z.B. DSGVO, spezifische Branchenrichtlinien, interne Compliance-Regeln",
        "type": "text"
    },
    {
        "id": "custom_scenarios",
        "question": "Gibt es spezifische Szenarien oder Fallbeispiele, die eingebaut werden sollen?",
        "description": "Beschreiben Sie relevante Situationen aus dem Arbeitsalltag Ihrer Einrichtung",
        "type": "text"
    }
]

# Hallucination management configuration
HALLUCINATION_MANAGEMENT = {
    "verification_enabled": True,
    "log_confidence_scores": True,
    "uncertainty_threshold": 0.7,  # Threshold for marking uncertain content
    "factuality_check": True,      # Enable factuality checking
    "source_attribution": True     # Enable source attribution in outputs
}