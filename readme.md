# Security Script Generator

Ein RAG-basierter Chatbot zur Erstellung maßgeschneiderter Schulungsskripte für Informationssicherheit im medizinischen Bereich.

## Übersicht

Die Security Script Generator-Anwendung ermöglicht die automatisierte Erstellung von E-Learning-Skripten für Informationssicherheitsschulungen, die speziell auf den medizinischen Kontext zugeschnitten sind. Der Chatbot führt strukturierte Gespräche mit dem Benutzer, um Anforderungen zu sammeln und generiert dann detaillierte Schulungsskripte basierend auf dem 7-Stufen-Kompetenzmodell.

### Hauptmerkmale

- **RAG-basierte Generierung**: Verwendet Retrieval-Augmented Generation, um fundierte und faktenbasierte Inhalte zu erstellen
- **Strukturierter Ansatz**: Folgt einem 7-Stufen-Template für die Skriptgenerierung, das alle wesentlichen Kompetenzbereiche der Informationssicherheit abdeckt
- **Kontextbezogene Anpassung**: Passt die Inhalte an spezifische medizinische Einrichtungen, Zielgruppen und Bedrohungsszenarien an
- **Integriertes Halluzinationsmanagement**: Reduziert das Risiko von Fehlinformationen durch aktives Halluzinationsmanagement
- **Web- und CLI-Schnittstellen**: Flexibler Zugang über Webbrowser oder Kommandozeile

## Technische Architektur

Die Anwendung basiert auf folgenden Komponenten:

1. **Frontend**: Ein responsives Web-Interface für die Interaktion mit dem Chatbot
2. **Chatbot-Engine**: Verwaltet den Dialog und orchestriert den Generierungsprozess
3. **RAG-System**: Kombiniert:
   - Vector Database: Speichert Einbettungen von Dokumenten, Vorlagen und Bedrohungsvektoren
   - Retrieval Controller: Führt semantische Suchen für relevanten Kontext durch
4. **LLM-Integration**: Verbindet sich mit Ollama für die Textgenerierung
5. **Template-System**: Strukturiert die Skripterstellung nach dem 7-Stufen-Modell

## Installation und Ausführung

### Voraussetzungen

- Docker und Docker Compose
- 8 GB RAM (mindestens)
- NVIDIA GPU (empfohlen für bessere Leistung)

### Mit Docker Compose

1. Klonen Sie das Repository:

   ```
   git clone https://github.com/your-username/securityscript-gen.git
   cd securityscript-gen
   ```

2. Starten Sie die Anwendung mit Docker Compose:

   ```
   docker-compose up -d
   ```

3. Öffnen Sie einen Webbrowser und navigieren Sie zu:
   ```
   http://localhost:8000
   ```

### Lokale Installation

1. Klonen Sie das Repository:

   ```
   git clone https://github.com/your-username/securityscript-gen.git
   cd securityscript-gen
   ```

2. Erstellen Sie eine virtuelle Umgebung und installieren Sie die Abhängigkeiten:

   ```
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Stellen Sie sicher, dass Ollama lokal installiert ist und läuft:

   ```
   # Auf einem anderen Terminal/Fenster
   ollama run mistral
   ```

4. Initialisieren Sie die Vector-Datenbank:

   ```
   python -m app.main init
   ```

5. Starten Sie die Anwendung:

   ```
   python -m app.main server
   ```

6. Alternativ können Sie die CLI-Version verwenden:
   ```
   python -m app.main cli
   ```

## Verwendung

1. Starten Sie eine neue Sitzung im Web-Interface oder CLI
2. Beantworten Sie die strategischen Fragen des Chatbots zu:
   - Art der medizinischen Einrichtung
   - Zielgruppe der Schulung
   - Dauer der Schulung
   - Schwerpunkt-Bedrohungen
   - Regulatorische Anforderungen
3. Prüfen Sie die Zusammenfassung der gesammelten Informationen
4. Lassen Sie das Schulungsskript generieren
5. Sehen Sie sich das generierte Skript an und nehmen Sie bei Bedarf Anpassungen vor
6. Exportieren Sie das Skript im gewünschten Format (Markdown oder JSON)

## 7-Stufen-Template

Das generierte Skript folgt diesem strukturierten Aufbau:

1. **Threat Awareness / Bedrohungsbewusstsein**: Kontext, in dem Bedrohungen auftreten
2. **Threat Identification / Bedrohungserkennung**: Indikatoren und Merkmale von Bedrohungen
3. **Threat Impact Assessment / Bedrohungsausmaß**: Mögliche Konsequenzen eines Angriffs
4. **Tactic Choice / Taktische Maßnahmenauswahl**: Handlungsoptionen bei erkannten Bedrohungen
5. **Tactic Justification / Maßnahmenrechtfertigung**: Begründung der empfohlenen Maßnahmen
6. **Tactic Mastery / Maßnahmenbeherrschung**: Detaillierte Anleitungen zur Umsetzung
7. **Tactic Check & Follow-Up / Anschlusshandlungen**: Nachkontrollen und weitere Maßnahmen

## Halluzinationsmanagement

Die Anwendung implementiert mehrere Strategien zur Reduzierung von Halluzinationen:

1. **Quellenattribution**: Nachverfolgung der Informationsquellen
2. **Faktenprüfung**: Validierung von Aussagen gegen den abgerufenen Kontext
3. **Unsicherheitsmarkierung**: Kennzeichnung von potenziell unsicheren Inhalten
4. **Überprüfung durch Experten**: Möglichkeit zur manuellen Revision

## Erweiterung der Wissensbasis

Um die Wissensdatenbank zu erweitern:

1. Fügen Sie neue Dokumente in die entsprechenden Unterverzeichnisse von `/data/documents/` ein:

   - `templates/`: Vorlagen und Beispielskripte
   - `papers/`: Forschungspapiere und Fachliteratur
   - `threats/`: Bedrohungsvektoren und Sicherheitsszenarien

2. Reinitialisieren Sie die Vector-Datenbank:
   ```
   python -m app.main init
   ```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe die LICENSE-Datei für Details.
