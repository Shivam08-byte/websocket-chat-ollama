import os
import io
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from fastapi import UploadFile, File

from rag_store import RAGStore
from app_langchain.langchain_rag import LangChainRAGSystem
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WebSocket Chat with Ollama")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get configuration from environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_CHARS = int(os.getenv("RAG_MAX_CHARS", "2000"))
RAG_STORE_PATH = os.getenv("RAG_STORE_PATH", "/app/data/rag_store.json")
RAG_SAVE_UPLOADS = os.getenv("RAG_SAVE_UPLOADS", "true").lower() in {"1", "true", "yes", "on"}
RAG_UPLOAD_DIR = os.getenv("RAG_UPLOAD_DIR", "/app/data/uploads")

# Current active model (can be changed via API)
current_model = OLLAMA_MODEL

# System selection: "manual" or "langchain"
current_system = "manual"  # Default to manual implementation

# Available models with descriptions
AVAILABLE_MODELS = {
    "gemma:2b": {
        "name": "Gemma 2B",
        "size": "1.7 GB",
        "description": "Google's efficient model, great for general conversations"
    },
    "phi3": {
        "name": "Phi-3 Mini",
        "size": "2.3 GB", 
        "description": "Microsoft's small model, excellent reasoning capabilities"
    },
    "llama3.2:1b": {
        "name": "Llama 3.2 1B",
        "size": "1.3 GB",
        "description": "Meta's compact model, fast and efficient"
    },
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 1.5B",
        "size": "934 MB",
        "description": "Alibaba's multilingual model, supports many languages"
    }
}

# Active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

# Initialize both RAG systems
rag_store = RAGStore(ollama_host=OLLAMA_HOST, embed_model=OLLAMA_EMBED_MODEL, store_path=RAG_STORE_PATH)
langchain_rag = LangChainRAGSystem(
    ollama_host=OLLAMA_HOST,
    ollama_model=current_model,
    embed_model=OLLAMA_EMBED_MODEL,
    chunk_size=800,
    chunk_overlap=200
)


async def query_ollama(prompt: str, sources: list | None = None, use_langchain: bool = False) -> str:
    """Query Ollama API and return response - supports both manual and LangChain systems"""
    
    # Route to LangChain system if requested
    if use_langchain:
        if sources and RAG_ENABLED:
            return await langchain_rag.query_with_rag(prompt, sources=sources, top_k=RAG_TOP_K)
        else:
            return await langchain_rag.query_without_rag(prompt)
    
    # Original manual implementation
    try:
        # Base system prompt
        system_prompt = "You are a helpful AI assistant. Provide clear, concise, and accurate responses. Prefer factual, sourced answers when context is provided."

        # Optional RAG context - only when specific sources are provided
        context_block = ""
        if RAG_ENABLED and sources:
            try:
                context_block = await rag_store.build_context(
                    prompt,
                    top_k=RAG_TOP_K,
                    max_chars=RAG_MAX_CHARS,
                    sources=sources,
                )
            except Exception:
                context_block = ""
        logging.info(
            "RAG context %s | sources=%s | context_chars=%s",
            "ENABLED" if context_block else "DISABLED",
            sources,
            len(context_block) if context_block else 0,
        )

        if context_block:
            full_prompt = (
                f"{system_prompt}\n\n"
                f"You are given retrieved context from a knowledge base. Use it to answer the question.\n"
                f"If the answer isn't in the context, say you don't know.\n\n"
                f"Context:\n{context_block}\n\n"
                f"User: {prompt}\nAssistant:"
            )
        else:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": current_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 200,  # Limit response length
                        "stop": ["\nUser:", "User:", "\n\n\n"]  # Stop at reasonable points
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "No response from model")
                # Clean up the response
                response_text = response_text.strip()
                return response_text if response_text else "I'm sorry, I couldn't generate a proper response."
            else:
                return f"Error: Received status code {response.status_code}"
                
    except httpx.ConnectError:
        return "Error: Cannot connect to Ollama. Make sure Ollama service is running."
    except Exception as e:
        return f"Error: {str(e)}"


@app.get("/")
async def get():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat communication"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_message(
            json.dumps({
                "type": "system",
                "message": "Connected to chat server. Type your message to chat with the AI."
            }),
            websocket
        )
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                sources = message_data.get("sources")
                use_langchain = message_data.get("useLangchain", False)  # Get system preference
                
                if isinstance(sources, list):
                    # Coerce to strings
                    sources = [str(s) for s in sources if isinstance(s, (str, bytes))]
                else:
                    sources = None
                
                system_type = "LangChain" if use_langchain else "Manual"
                logging.info("WS message received | system=%s | sources=%s | text_preview=%s", 
                           system_type, sources, user_message[:80])
                
                if not user_message.strip():
                    continue
                
                # Echo user message
                await manager.send_message(
                    json.dumps({
                        "type": "user",
                        "message": user_message
                    }),
                    websocket
                )
                
                # Send typing indicator
                await manager.send_message(
                    json.dumps({
                        "type": "typing",
                        "message": f"AI is typing... ({system_type} system)"
                    }),
                    websocket
                )
                
                # Get AI response with selected system
                ai_response = await query_ollama(user_message, sources=sources, use_langchain=use_langchain)
                
                # Send AI response
                await manager.send_message(
                    json.dumps({
                        "type": "ai",
                        "message": ai_response
                    }),
                    websocket
                )
                
            except json.JSONDecodeError:
                await manager.send_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid message format"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ollama_host": OLLAMA_HOST,
        "ollama_model": current_model,
        "ollama_timeout": OLLAMA_TIMEOUT,
        "rag_enabled": RAG_ENABLED,
        "embed_model": OLLAMA_EMBED_MODEL
    }


@app.get("/api/models")
async def get_available_models():
    """Get list of available models"""
    return {
        "current_model": current_model,
        "available_models": AVAILABLE_MODELS
    }


@app.post("/api/models/load")
async def load_model(model_data: dict):
    """Load a specific model"""
    global current_model
    
    model_name = model_data.get("model")
    
    if not model_name or model_name not in AVAILABLE_MODELS:
        return {
            "success": False,
            "message": f"Invalid model. Available models: {', '.join(AVAILABLE_MODELS.keys())}"
        }
    
    try:
        # Check if model is already pulled
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Pull the model if not available
            pull_response = await client.post(
                f"{OLLAMA_HOST}/api/pull",
                json={"name": model_name}
            )
            
            if pull_response.status_code == 200:
                current_model = model_name
                return {
                    "success": True,
                    "message": f"Model {model_name} loaded successfully",
                    "current_model": current_model
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to load model: {pull_response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Error loading model: {str(e)}"
        }


# -------- RAG endpoints --------

@app.get("/api/rag/stats")
async def rag_stats():
    """Get stats from both RAG systems"""
    manual_stats = {"enabled": RAG_ENABLED, **rag_store.stats()}
    langchain_stats = langchain_rag.stats()
    
    return {
        "manual": manual_stats,
        "langchain": langchain_stats,
        "current_system": current_system
    }


@app.post("/api/system/switch")
async def switch_system(payload: dict):
    """Switch between manual and langchain systems"""
    global current_system
    system = payload.get("system", "manual")
    
    if system not in ["manual", "langchain"]:
        return {"success": False, "message": "Invalid system. Choose 'manual' or 'langchain'"}
    
    current_system = system
    logging.info(f"Switched to {system} system")
    
    return {
        "success": True,
        "current_system": current_system,
        "message": f"Switched to {system} system"
    }


@app.get("/api/system/current")
async def get_current_system():
    """Get the currently active system"""
    return {
        "current_system": current_system,
        "available_systems": ["manual", "langchain"]
    }


@app.post("/api/rag/ingest_text")
async def rag_ingest_text(payload: dict):
    text = payload.get("text", "")
    source = payload.get("source", "uploaded")
    if not text.strip():
        return {"success": False, "message": "No text provided"}
    try:
        added = await rag_store.add_text(text, source=source)
        return {"success": True, "added_chunks": added}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/rag/ingest_file")
async def rag_ingest_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename or "uploaded"
        logging.info("/api/rag/ingest_file received | filename=%s | bytes=%s", filename, len(content) if content else 0)
        # Optionally save original upload to disk for inspection
        try:
            if RAG_SAVE_UPLOADS and filename:
                os.makedirs(RAG_UPLOAD_DIR, exist_ok=True)
                save_path = os.path.join(RAG_UPLOAD_DIR, filename)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logging.info("Saved upload to %s", save_path)
        except Exception:
            # Non-fatal: continue even if saving fails
            pass
        ext = os.path.splitext(filename)[1].lower()

        # Determine how to extract text based on extension
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                pages = []
                for p in reader.pages:
                    pages.append(p.extract_text() or "")
                text = "\n\n".join(pages)
                if not text.strip():
                    logging.warning("PDF contained no extractable text: %s", filename)
                    return {"success": False, "message": "No text extracted from PDF. If it's scanned, try a text-based file."}
            except Exception as e:
                return {"success": False, "message": f"PDF parse error: {str(e)}"}
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text = "\n".join(para.text for para in doc.paragraphs)
                if not text.strip():
                    logging.warning("DOCX contained no extractable text: %s", filename)
                    return {"success": False, "message": "No text extracted from DOCX. Please upload a text-rich document."}
            except Exception as e:
                return {"success": False, "message": f"DOCX parse error: {str(e)}"}
        else:
            # Treat as text/markdown
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                text = content.decode("latin-1", errors="ignore")
            if not text.strip():
                logging.warning("Text/Markdown contained no extractable text: %s", filename)
                return {"success": False, "message": "No text extracted from file. Please upload a non-empty text file."}

        # Index in BOTH systems for comparison
        added_manual = await rag_store.add_text(text, source=filename)
        added_langchain = langchain_rag.add_documents(text, source=filename)
        
        logging.info("Indexed upload | filename=%s | manual_chunks=%s | langchain_chunks=%s", 
                    filename, added_manual, added_langchain)
        
        if added_manual <= 0 and added_langchain <= 0:
            return {"success": False, "message": "No chunks indexed (file may be empty or unsupported)."}
        
        return {
            "success": True, 
            "added_chunks": added_manual,
            "added_chunks_langchain": added_langchain,
            "source": filename
        }
    except Exception as e:
        logging.exception("Ingest file failed: %s", e)
        return {"success": False, "message": str(e)}


@app.post("/api/rag/preview")
async def rag_preview(payload: dict):
    """Preview retrieved context for a given query and optional sources.
    Body: { "query": str, "sources": [str], "top_k": int }
    """
    try:
        query = payload.get("query", "").strip()
        sources = payload.get("sources")
        top_k = int(payload.get("top_k", RAG_TOP_K))
        if not query:
            return {"success": False, "message": "No query provided"}
        if sources and isinstance(sources, list):
            sources = [str(s) for s in sources]
        else:
            sources = None
        ctx = await rag_store.build_context(query, top_k=top_k, max_chars=RAG_MAX_CHARS, sources=sources)
        return {"success": True, "sources": sources, "top_k": top_k, "context_preview": ctx[:1000], "context_chars": len(ctx)}
    except Exception as e:
        return {"success": False, "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)
