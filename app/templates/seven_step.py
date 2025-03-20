"""
Seven-Step Template for security training scripts.
This module provides the template structure and helper functions for script generation.
"""

from typing import Dict, List, Any, Optional

# Template structure with guidelines for each section
TEMPLATE = {
    "threat_awareness": {
        "title": "Threat Awareness / Bedrohungsbewusstsein",
        "description": "Beschreibung des Kontextes, in dem Bedrohungen auftreten",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Ein realistisches Szenario aus dem medizinischen Arbeitsalltag beschrieben werden
        - Der Kontext, in dem die Sicherheitsbedrohung auftreten kann, dargestellt werden
        - Ein Beispiel für vorbildliches Verhalten (Social Learning Theory) integriert werden
        - Die Relevanz des Themas für die spezifische Zielgruppe deutlich gemacht werden
        
        Stil: Narrativ, persönlich ansprechend, mit konkretem Bezug zur Arbeitssituation
        Länge: 150-250 Wörter
        """
    },
    "threat_identification": {
        "title": "Threat Identification / Bedrohungserkennung",
        "description": "Aufzeigen, welche Indikatoren auf eine Bedrohung hinweisen",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Konkrete Erkennungsmerkmale der Bedrohung aufgelistet werden
        - Visuelle und inhaltliche Warnsignale beschrieben werden
        - Beispiele für typische Angriffsszenarien gegeben werden
        - Beobachtungslernen durch Zitate oder Beispiele von erfahrenen Kollegen eingebaut werden
        
        Stil: Klar strukturiert, mit nummerierter oder Aufzählungsliste für die Erkennungsmerkmale
        Länge: 200-300 Wörter
        """
    },
    "threat_impact": {
        "title": "Threat Impact Assessment / Bedrohungsausmaß",
        "description": "Konkrete Darstellung der möglichen Folgen eines Angriffs",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Realistische Konsequenzen für Patienten, Mitarbeiter und die Einrichtung dargestellt werden
        - Der potenzielle Schaden in verschiedenen Dimensionen (Sicherheit, Finanzen, Reputation) beschrieben werden
        - Wenn möglich, ein reales Beispiel oder Fallstudie aus dem Gesundheitssektor integriert werden
        - Protection Motivation Theory angewendet werden: die Bedrohung als schwerwiegend aber bewältigbar darstellen
        
        Stil: Sachlich aber eindringlich, Folgen nach Stakeholdern gegliedert
        Länge: 200-300 Wörter
        """
    },
    "tactic_choice": {
        "title": "Tactic Choice / Taktische Maßnahmenauswahl",
        "description": "Übersicht möglicher Handlungsoptionen bei Erkennen einer Bedrohung",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Verschiedene mögliche Reaktionen auf die Bedrohung präsentiert werden
        - Eine klare Empfehlung für die beste Vorgehensweise gegeben werden
        - Die unterschiedlichen Handlungsoptionen in einer logischen Reihenfolge dargestellt werden
        - Der Entscheidungsprozess für die Auswahl der richtigen Taktik erläutert werden
        
        Stil: Strukturierte Darstellung der Optionen, klare Handlungsanweisung
        Länge: 150-250 Wörter
        """
    },
    "tactic_justification": {
        "title": "Tactic Justification / Maßnahmenrechtfertigung",
        "description": "Begründung, warum die gewählte Maßnahme besonders effektiv ist",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Begründet werden, warum die empfohlene Vorgehensweise die beste Option ist
        - Die Wirksamkeit der Maßnahme mit Fakten oder Beispielen belegt werden
        - Die Konsequenzen alternativer Handlungsweisen aufgezeigt werden
        - Protection Motivation Theory angewendet werden: die Selbstwirksamkeit und Handlungsfähigkeit betonen
        
        Stil: Überzeugend, evidenzbasiert, mit konkreten Beispielen aus dem medizinischen Umfeld
        Länge: 150-250 Wörter
        """
    },
    "tactic_mastery": {
        "title": "Tactic Mastery / Maßnahmenbeherrschung",
        "description": "Detaillierte Schritt-für-Schritt-Anleitung zur Umsetzung der gewählten Maßnahme",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Eine präzise, schrittweise Anleitung zur Durchführung der Sicherheitsmaßnahme gegeben werden
        - Konkrete Handlungsschritte nummeriert und in chronologischer Reihenfolge dargestellt werden
        - Potenzielle Herausforderungen oder Fallstricke bei der Umsetzung angesprochen werden
        - Social Learning Theory angewendet werden: das gewünschte Verhalten klar demonstrieren
        
        Stil: Präzise, anleitend, mit klaren Schritt-für-Schritt-Anweisungen
        Länge: 250-350 Wörter
        """
    },
    "tactic_followup": {
        "title": "Tactic Check & Follow-Up / Anschlusshandlungen",
        "description": "Festlegung von Nachkontrollen und weiteren Maßnahmen",
        "guidelines": """
        In diesem Abschnitt sollte:
        - Notwendige Folgeaktionen nach der Hauptmaßnahme beschrieben werden
        - Verfahren zur Verifizierung des Erfolgs der Maßnahme dargestellt werden
        - Hinweise zur Dokumentation und zum Meldewesen gegeben werden
        - Die kontinuierliche Verbesserung der Sicherheit als Prozess betont werden
        
        Stil: Zukunftsorientiert, prozessbezogen, mit Betonung auf kontinuierliche Verbesserung
        Länge: 150-250 Wörter
        """
    }
}

def get_template_structure() -> Dict[str, Dict[str, str]]:
    """
    Get the template structure without the guidelines.
    
    Returns:
        Dictionary with the template structure
    """
    template_structure = {}
    for key, section in TEMPLATE.items():
        template_structure[key] = {
            "title": section["title"],
            "description": section["description"]
        }
    
    return template_structure

def get_section_guidelines(section_key: str) -> str:
    """
    Get the guidelines for a specific section.
    
    Args:
        section_key: Key of the section
        
    Returns:
        Guidelines string for the section
    """
    if section_key in TEMPLATE:
        return TEMPLATE[section_key]["guidelines"].strip()
    return ""

def get_section_title(section_key: str) -> str:
    """
    Get the title for a specific section.
    
    Args:
        section_key: Key of the section
        
    Returns:
        Title string for the section
    """
    if section_key in TEMPLATE:
        return TEMPLATE[section_key]["title"]
    return section_key.replace("_", " ").title()

def get_section_description(section_key: str) -> str:
    """
    Get the description for a specific section.
    
    Args:
        section_key: Key of the section
        
    Returns:
        Description string for the section
    """
    if section_key in TEMPLATE:
        return TEMPLATE[section_key]["description"]
    return ""

def create_script_template(threat_type: str, facility_type: str, audience: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Create a script template with placeholders for specific context.
    
    Args:
        threat_type: Type of security threat
        facility_type: Type of medical facility
        audience: Target audience list
        
    Returns:
        Template dictionary with placeholders
    """
    audience_str = ", ".join(audience) if isinstance(audience, list) else audience
    
    template = {}
    for key, section in TEMPLATE.items():
        template[key] = {
            "title": section["title"],
            "content": f"[Hier {section['title']} zum Thema {threat_type} für {audience_str} in {facility_type} einfügen]"
        }
    
    return template

def validate_script_sections(script_sections: Dict[str, str]) -> List[str]:
    """
    Validate script sections against the template.
    
    Args:
        script_sections: Dictionary of script sections
        
    Returns:
        List of missing or incomplete sections
    """
    missing_sections = []
    
    for key in TEMPLATE.keys():
        if key not in script_sections:
            missing_sections.append(key)
        elif not script_sections[key] or len(script_sections[key]) < 100:
            missing_sections.append(f"{key} (unvollständig)")
    
    return missing_sections

def format_script_as_markdown(script_sections: Dict[str, Dict[str, str]], metadata: Dict[str, Any]) -> str:
    """
    Format script sections as a Markdown document.
    
    Args:
        script_sections: Dictionary of script sections
        metadata: Script metadata
        
    Returns:
        Formatted Markdown string
    """
    # Create title
    threat_type = metadata.get("focus_threats", "Informationssicherheit")
    facility_type = metadata.get("facility_type", "medizinische Einrichtung")
    audience = metadata.get("target_audience", "")
    audience_str = ", ".join(audience) if isinstance(audience, list) else audience
    
    title = f"# Schulungsskript: {threat_type} für {audience_str} in {facility_type}"
    
    # Add metadata section
    markdown_parts = [title, "\n\n## Metadaten\n"]
    for key, value in metadata.items():
        if value:
            markdown_parts.append(f"- **{key}**: {value}")
    
    # Add content sections
    for key in TEMPLATE.keys():
        if key in script_sections:
            section = script_sections[key]
            title = section.get("title", TEMPLATE[key]["title"])
            content = section.get("content", "")
            
            markdown_parts.append(f"\n\n## {title}\n\n{content}")
    
    return "\n".join(markdown_parts)