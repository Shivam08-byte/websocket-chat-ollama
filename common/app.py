"""
Common FastAPI router for shared endpoints:
- Health check
- Model management
- System switching
"""

import os
import httpx
from fastapi import APIRouter

# Create router for common endpoints
router = APIRouter(prefix="", tags=["common"])

# Get configuration from environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

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


@router.get("/health")
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


@router.get("/api/models")
async def get_available_models():
    """Get list of available models"""
    return {
        "current_model": current_model,
        "available_models": AVAILABLE_MODELS
    }


@router.post("/api/models/load")
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


@router.post("/api/system/switch")
async def switch_system(payload: dict):
    """Switch between manual and langchain systems"""
    global current_system
    system = payload.get("system", "manual")
    
    if system not in ["manual", "langchain"]:
        return {"success": False, "message": "Invalid system. Choose 'manual' or 'langchain'"}
    
    current_system = system
    import logging
    logging.info(f"[Common] Switched to {system} system")
    
    return {
        "success": True,
        "current_system": current_system,
        "message": f"Switched to {system} system"
    }


@router.get("/api/system/current")
async def get_current_system():
    """Get the currently active system"""
    return {
        "current_system": current_system,
        "available_systems": ["manual", "langchain"]
    }
