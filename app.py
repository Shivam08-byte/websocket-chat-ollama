"""
Main FastAPI Server - Clean Orchestrator
Minimal orchestration layer that coordinates all sub-applications
"""

import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import sub-app routers
from common.app import router as common_router
from common.unified_rag import router as unified_rag_router, init_unified_rag
from common.websocket_handler import ConnectionManager, WebSocketHandler
from common.query_service import QueryService
from app_manual.app import router as manual_router, get_rag_store
from app_langchain.app import router as langchain_router, get_langchain_rag
from app_agents.app import router as agents_router

logging.basicConfig(level=logging.INFO)

# Initialize main FastAPI application
app = FastAPI(
    title="WebSocket Chat with Ollama - Modular Architecture",
    description="Modular RAG system with Manual and LangChain implementations",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register all sub-app routers
app.include_router(common_router)           # Health, models, system switching
app.include_router(unified_rag_router)      # Unified RAG endpoints
app.include_router(manual_router)           # Manual RAG endpoints
app.include_router(langchain_router)        # LangChain RAG endpoints
app.include_router(agents_router)           # AI Agents endpoints

logging.info("[Server] Registered routers: common, unified_rag, manual, langchain, agents")

# Get configuration
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")

# Initialize RAG systems
rag_store = get_rag_store()
langchain_rag = get_langchain_rag()

# Initialize unified RAG router with both systems
init_unified_rag(rag_store, langchain_rag)

# Initialize query service
query_service = QueryService(rag_store, langchain_rag, OLLAMA_MODEL)

# Initialize WebSocket components
connection_manager = ConnectionManager()
websocket_handler = WebSocketHandler(connection_manager, query_service)


@app.get("/")
async def serve_frontend():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/agents/agent1")
async def serve_agent1():
    """Serve Agent1 demo page"""
    with open("static/agent1.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket_handler.handle_connection(websocket)


if __name__ == "__main__":
    import uvicorn
    logging.info("[Server] Starting modular FastAPI application")
    logging.info("[Server] Frontend: http://localhost:%s", FASTAPI_PORT)
    logging.info("[Server] API Docs: http://localhost:%s/docs", FASTAPI_PORT)
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)
