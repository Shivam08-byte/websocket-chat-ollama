"""
Manual RAG FastAPI router with all related endpoints
"""

import os
import io
import logging
from fastapi import APIRouter, UploadFile, File

from .rag_store import RAGStore

# Create router for manual RAG endpoints
router = APIRouter(prefix="/api/rag/manual", tags=["manual-rag"])

# Get configuration from environment variables
BASE_DATA_DIR = os.getenv("DATA_CONTAINER_DIR", "/app/data")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_STORE_PATH = os.getenv("RAG_STORE_PATH", os.path.join(BASE_DATA_DIR, "rag_store.json"))
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_CHARS = int(os.getenv("RAG_MAX_CHARS", "2000"))
RAG_SAVE_UPLOADS = os.getenv("RAG_SAVE_UPLOADS", "true").lower() in {"1", "true", "yes", "on"}
RAG_UPLOAD_DIR = os.getenv("RAG_UPLOAD_DIR", os.path.join(BASE_DATA_DIR, "uploads"))

# Initialize Manual RAG system
rag_store = RAGStore(
    ollama_host=OLLAMA_HOST, 
    embed_model=OLLAMA_EMBED_MODEL, 
    store_path=RAG_STORE_PATH
)

logging.basicConfig(level=logging.INFO)
logging.info("[Manual RAG] Initialized with embed_model=%s, store_path=%s", 
             OLLAMA_EMBED_MODEL, RAG_STORE_PATH)


@router.get("/stats")
async def manual_rag_stats():
    """Get stats from manual RAG system"""
    manual_stats = {"enabled": RAG_ENABLED, **rag_store.stats()}
    return manual_stats


@router.post("/ingest_text")
async def manual_ingest_text(payload: dict):
    """Ingest raw text into manual RAG system"""
    text = payload.get("text", "")
    source = payload.get("source", "uploaded")
    if not text.strip():
        return {"success": False, "message": "No text provided"}
    try:
        added = await rag_store.add_text(text, source=source)
        return {"success": True, "added_chunks": added, "system": "manual"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/ingest_file")
async def manual_ingest_file(file: UploadFile = File(...)):
    """Ingest file into manual RAG system"""
    try:
        content = await file.read()
        filename = file.filename or "uploaded"
        logging.info("[Manual RAG] /ingest_file received | filename=%s | bytes=%s", 
                    filename, len(content) if content else 0)
        
        # Optionally save original upload to disk
        try:
            if RAG_SAVE_UPLOADS and filename:
                os.makedirs(RAG_UPLOAD_DIR, exist_ok=True)
                save_path = os.path.join(RAG_UPLOAD_DIR, filename)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logging.info("[Manual RAG] Saved upload to %s", save_path)
        except Exception:
            pass  # Non-fatal
        
        ext = os.path.splitext(filename)[1].lower()

        # Extract text based on extension
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                pages = []
                for p in reader.pages:
                    pages.append(p.extract_text() or "")
                text = "\n\n".join(pages)
                if not text.strip():
                    logging.warning("[Manual RAG] PDF contained no extractable text: %s", filename)
                    return {"success": False, "message": "No text extracted from PDF"}
            except Exception as e:
                return {"success": False, "message": f"PDF parse error: {str(e)}"}
        
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text = "\n".join(para.text for para in doc.paragraphs)
                if not text.strip():
                    logging.warning("[Manual RAG] DOCX contained no extractable text: %s", filename)
                    return {"success": False, "message": "No text extracted from DOCX"}
            except Exception as e:
                return {"success": False, "message": f"DOCX parse error: {str(e)}"}
        
        else:
            # Treat as text/markdown
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                text = content.decode("latin-1", errors="ignore")
            if not text.strip():
                logging.warning("[Manual RAG] Text file contained no extractable text: %s", filename)
                return {"success": False, "message": "No text extracted from file"}

        # Index in manual system
        added = await rag_store.add_text(text, source=filename)
        
        logging.info("[Manual RAG] Indexed upload | filename=%s | chunks=%s", filename, added)
        
        if added <= 0:
            return {"success": False, "message": "No chunks indexed (file may be empty)"}
        
        return {
            "success": True, 
            "added_chunks": added,
            "source": filename,
            "system": "manual"
        }
    except Exception as e:
        logging.exception("[Manual RAG] Ingest file failed: %s", e)
        return {"success": False, "message": str(e)}


@router.post("/preview")
async def manual_rag_preview(payload: dict):
    """Preview retrieved context for a given query and optional sources"""
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
        
        ctx = await rag_store.build_context(
            query, 
            top_k=top_k, 
            max_chars=RAG_MAX_CHARS, 
            sources=sources
        )
        
        return {
            "success": True, 
            "sources": sources, 
            "top_k": top_k, 
            "context_preview": ctx[:1000], 
            "context_chars": len(ctx),
            "system": "manual"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# Export rag_store for use in main app
def get_rag_store():
    """Get the initialized RAG store instance"""
    return rag_store
