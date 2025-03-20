"""
Main application module that ties all components together.
This is the entry point for the application.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse
import sys
import time
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

from app.config import HOST, PORT, DEBUG, DOCS_DIR, DATA_DIR, VECTOR_DB_PATH
from app.utils import system_logger, generate_session_id, format_as_markdown
from app.chatbot.engine import chatbot_engine
from app.data.vector_store import vector_store
from app.data.loader import document_loader
from app.rag.controller import rag_controller
from app.llm.ollama_client import ollama_client

# Initialize FastAPI app
app = FastAPI(
    title="Security Script Generator",
    description="Generate information security training scripts for medical contexts",
    version="1.0.0",
    debug=DEBUG
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "frontend" / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=Path(__file__).parent / "frontend" / "templates")

# Pydantic models for request validation
class MessageRequest(BaseModel):
    """Model for chat message requests."""
    session_id: str
    message: str

class NewSessionRequest(BaseModel):
    """Model for creating a new session."""
    pass

class GenerateScriptRequest(BaseModel):
    """Model for script generation requests."""
    session_id: str

class ExportScriptRequest(BaseModel):
    """Model for script export requests."""
    session_id: str
    format: str = Field(default="markdown")

# API Routes
@app.get("/")
async def get_index(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/sessions")
async def create_session():
    """Create a new chat session."""
    session_id = chatbot_engine.create_session()
    introduction = chatbot_engine.get_introduction_message(session_id)
    
    return {
        "session_id": session_id,
        "message": introduction
    }

@app.post("/api/messages")
async def send_message(request: MessageRequest):
    """Process a chat message and return the response."""
    session_id = request.session_id
    message = request.message
    
    # Process message
    response = chatbot_engine.process_message(session_id, message)
    
    return {
        "session_id": session_id,
        "message": response
    }

@app.post("/api/generate-script")
async def generate_script(request: GenerateScriptRequest):
    """Generate a script for a session."""
    session_id = request.session_id
    
    # Check if the session exists
    session = chatbot_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Generate script
    response = chatbot_engine._generate_script(session_id)
    
    return {
        "session_id": session_id,
        "message": response,
        "status": "generated"
    }

@app.get("/api/script/{session_id}")
async def get_script(session_id: str):
    """Get the generated script for a session."""
    # Check if the session exists
    session = chatbot_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the generated script
    script = chatbot_engine.get_generated_script(session_id)
    
    return {
        "session_id": session_id,
        "script": script
    }

@app.post("/api/export-script")
async def export_script(request: ExportScriptRequest):
    """Export the generated script in the specified format."""
    session_id = request.session_id
    export_format = request.format
    
    # Check if the session exists
    session = chatbot_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the generated script
    generated_script = session.get("generated_script", "")
    if not generated_script:
        raise HTTPException(status_code=400, detail="No script has been generated for this session")
    
    # Export path
    export_dir = DATA_DIR / "exports"
    export_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if export_format == "markdown":
        # Export as Markdown
        export_path = export_dir / f"script_{session_id}_{timestamp}.md"
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(generated_script)
        
        return FileResponse(
            path=export_path,
            filename=f"script_{timestamp}.md",
            media_type="text/markdown"
        )
    elif export_format == "json":
        # Export as JSON
        export_path = export_dir / f"script_{session_id}_{timestamp}.json"
        
        # Parse the script into sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in generated_script.split("\n"):
            if line.startswith("## "):
                # Save previous section if exists
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                    current_content = []
                
                # Start new section
                current_section = line[3:].strip()
            elif current_section:
                current_content.append(line)
        
        # Save the last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        
        # Create JSON structure
        script_json = {
            "metadata": {
                "session_id": session_id,
                "generated_at": timestamp,
                "facility_type": session.get("strategic_responses", {}).get("facility_type", ""),
                "target_audience": session.get("strategic_responses", {}).get("target_audience", ""),
                "focus_threats": session.get("strategic_responses", {}).get("focus_threats", "")
            },
            "sections": sections
        }
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(script_json, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            path=export_path,
            filename=f"script_{timestamp}.json",
            media_type="application/json"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

@app.post("/api/customize-section")
async def customize_section(request: dict):
    """Customize a specific section of the script."""
    session_id = request.get("session_id")
    section_key = request.get("section_key")
    customization_request = request.get("customization")
    
    if not session_id or not section_key or not customization_request:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # Check if the session exists
    session = chatbot_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Customize the section
    response = chatbot_engine.customize_script_section(session_id, section_key, customization_request)
    
    return {
        "session_id": session_id,
        "message": response
    }

# WebSocket for real-time chat
@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket connections for real-time chat."""
    await websocket.accept()
    
    try:
        # Check if session exists, create if not
        if not chatbot_engine.get_session(session_id):
            session_id = chatbot_engine.create_session()
            introduction = chatbot_engine.get_introduction_message(session_id)
            await websocket.send_json({
                "type": "message",
                "session_id": session_id,
                "role": "assistant",
                "content": introduction
            })
        
        # Main WebSocket loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "")
            
            if message_type == "message":
                user_message = data.get("content", "")
                
                # Process message
                response = chatbot_engine.process_message(session_id, user_message)
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "session_id": session_id,
                    "role": "assistant",
                    "content": response
                })
            
            elif message_type == "generate":
                # Generate script
                response = chatbot_engine._generate_script(session_id)
                
                # Send response
                await websocket.send_json({
                    "type": "generation_complete",
                    "session_id": session_id,
                    "message": response
                })
            
            elif message_type == "ping":
                # Simple ping to keep connection alive
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        system_logger.info(f"WebSocket connection closed for session {session_id}")
    except Exception as e:
        system_logger.error(f"WebSocket error for session {session_id}: {e}")
        await websocket.close()

# Admin routes for managing documents and vector store
@app.post("/api/admin/documents")
async def add_document(request: dict):
    """Add a document to the vector store."""
    if DEBUG:  # Only available in debug mode
        filepath = request.get("filepath")
        collection = request.get("collection", "papers")
        metadata = request.get("metadata", {})
        
        if not filepath:
            raise HTTPException(status_code=400, detail="Missing filepath parameter")
        
        # Load document
        doc_id = document_loader.load_document(filepath, collection, metadata)
        
        if doc_id:
            return {"status": "success", "document_id": doc_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to load document")
    else:
        raise HTTPException(status_code=403, detail="Admin routes are only available in debug mode")

@app.post("/api/admin/load-directory")
async def load_directory(request: dict):
    """Load all documents in a directory into the vector store."""
    if DEBUG:  # Only available in debug mode
        directory = request.get("directory")
        collection = request.get("collection", "papers")
        recursive = request.get("recursive", True)
        
        if not directory:
            raise HTTPException(status_code=400, detail="Missing directory parameter")
        
        # Load directory
        doc_ids = document_loader.load_directory(directory, collection, recursive)
        
        return {"status": "success", "documents_loaded": len(doc_ids)}
    else:
        raise HTTPException(status_code=403, detail="Admin routes are only available in debug mode")

@app.post("/api/admin/threatmap")
async def load_threatmap(request: dict):
    """Load a threat map JSON file into the vector store."""
    if DEBUG:  # Only available in debug mode
        filepath = request.get("filepath")
        
        if not filepath:
            raise HTTPException(status_code=400, detail="Missing filepath parameter")
        
        # Load threat map
        doc_ids = document_loader.load_threatmap(filepath)
        
        return {"status": "success", "threats_loaded": len(doc_ids)}
    else:
        raise HTTPException(status_code=403, detail="Admin routes are only available in debug mode")

# CLI command handlers
def init_vector_store(args):
    """Initialize the vector store with example documents."""
    print("Initializing vector store...")
    
    # Ensure vector store directory exists
    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    
    # Load example documents
    examples_dir = DOCS_DIR / "examples"
    if examples_dir.exists():
        print(f"Loading examples from {examples_dir}...")
        document_loader.load_directory(examples_dir, "templates")
    
    # Load templates
    templates_dir = DOCS_DIR / "templates"
    if templates_dir.exists():
        print(f"Loading templates from {templates_dir}...")
        document_loader.load_directory(templates_dir, "templates")
    
    # Load papers
    papers_dir = DOCS_DIR / "papers"
    if papers_dir.exists():
        print(f"Loading papers from {papers_dir}...")
        document_loader.load_directory(papers_dir, "papers")
    
    # Load threats
    threats_file = DOCS_DIR / "threats" / "threat_map.json"
    if threats_file.exists():
        print(f"Loading threats from {threats_file}...")
        document_loader.load_threatmap(threats_file)
    
    print("Vector store initialization complete!")

def run_server(args):
    """Run the web server."""
    print(f"Starting server on {HOST}:{PORT}...")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)

def run_cli(args):
    """Run the application in CLI mode."""
    print("Starting CLI mode...")
    
    # Create a session
    session_id = chatbot_engine.create_session()
    print(chatbot_engine.get_introduction_message(session_id))
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting CLI mode.")
                break
            
            # Process message
            response = chatbot_engine.process_message(session_id, user_input)
            print(f"\nAssistant: {response}")
            
            # Check if we've generated a script
            session = chatbot_engine.get_session(session_id)
            if session and session.get("generated_script") and session.get("stage") == "followup":
                save = input("\nDo you want to save the generated script? (y/n): ")
                if save.lower() in ["y", "yes"]:
                    # Save the script
                    export_dir = DATA_DIR / "exports"
                    export_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    export_path = export_dir / f"script_{session_id}_{timestamp}.md"
                    
                    with open(export_path, "w", encoding="utf-8") as f:
                        f.write(session["generated_script"])
                    
                    print(f"Script saved to {export_path}")
        
        except KeyboardInterrupt:
            print("\nExiting CLI mode.")
            break
        
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Security Script Generator")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize the vector store")
    init_parser.set_defaults(func=init_vector_store)
    
    # server command
    server_parser = subparsers.add_parser("server", help="Run the web server")
    server_parser.set_defaults(func=run_server)
    
    # cli command
    cli_parser = subparsers.add_parser("cli", help="Run in CLI mode")
    cli_parser.set_defaults(func=run_cli)
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to running the server
        run_server(args)
    else:
        args.func(args)

if __name__ == "__main__":
    main()