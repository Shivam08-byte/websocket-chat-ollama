"""
LangChain RAG FastAPI router with all related endpoints
"""

import os
import io
import logging
from fastapi import APIRouter, UploadFile, File

from .langchain_rag import LangChainRAGSystem

# Create router for LangChain RAG endpoints
router = APIRouter(prefix="/api/rag/langchain", tags=["langchain-rag"])

# Get configuration from environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_SAVE_UPLOADS = os.getenv("RAG_SAVE_UPLOADS", "true").lower() in {"1", "true", "yes", "on"}
RAG_UPLOAD_DIR = os.getenv("RAG_UPLOAD_DIR", "/app/data/uploads")

# Initialize LangChain RAG system
langchain_rag = LangChainRAGSystem(
    ollama_host=OLLAMA_HOST,
    ollama_model=OLLAMA_MODEL,
    embed_model=OLLAMA_EMBED_MODEL,
    chunk_size=800,
    chunk_overlap=200
)

logging.basicConfig(level=logging.INFO)
logging.info("[LangChain RAG] Initialized with model=%s, embed_model=%s", 
             OLLAMA_MODEL, OLLAMA_EMBED_MODEL)


@router.get("/stats")
async def langchain_rag_stats():
    """Get stats from LangChain RAG system"""
    langchain_stats = langchain_rag.stats()
    return langchain_stats


@router.post("/ingest_text")
async def langchain_ingest_text(payload: dict):
    """Ingest raw text into LangChain RAG system"""
    text = payload.get("text", "")
    source = payload.get("source", "uploaded")
    if not text.strip():
        return {"success": False, "message": "No text provided"}
    try:
        added = langchain_rag.add_documents(text, source=source)
        return {"success": True, "added_chunks": added, "system": "langchain"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/ingest_file")
async def langchain_ingest_file(file: UploadFile = File(...)):
    """Ingest file into LangChain RAG system"""
    try:
        content = await file.read()
        filename = file.filename or "uploaded"
        logging.info("[LangChain RAG] /ingest_file received | filename=%s | bytes=%s", 
                    filename, len(content) if content else 0)
        
        # Optionally save original upload to disk
        try:
            if RAG_SAVE_UPLOADS and filename:
                os.makedirs(RAG_UPLOAD_DIR, exist_ok=True)
                save_path = os.path.join(RAG_UPLOAD_DIR, filename)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logging.info("[LangChain RAG] Saved upload to %s", save_path)
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
                    logging.warning("[LangChain RAG] PDF contained no extractable text: %s", filename)
                    return {"success": False, "message": "No text extracted from PDF"}
            except Exception as e:
                return {"success": False, "message": f"PDF parse error: {str(e)}"}
        
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text = "\n".join(para.text for para in doc.paragraphs)
                if not text.strip():
                    logging.warning("[LangChain RAG] DOCX contained no extractable text: %s", filename)
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
                logging.warning("[LangChain RAG] Text file contained no extractable text: %s", filename)
                return {"success": False, "message": "No text extracted from file"}

        # Index in LangChain system
        added = langchain_rag.add_documents(text, source=filename)
        
        logging.info("[LangChain RAG] Indexed upload | filename=%s | chunks=%s", filename, added)
        
        if added <= 0:
            return {"success": False, "message": "No chunks indexed (file may be empty)"}
        
        return {
            "success": True, 
            "added_chunks": added,
            "source": filename,
            "system": "langchain"
        }
    except Exception as e:
        logging.exception("[LangChain RAG] Ingest file failed: %s", e)
        return {"success": False, "message": str(e)}


@router.post("/query")
async def langchain_query(payload: dict):
    """Query LangChain RAG system"""
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
        
        # Query with RAG if sources provided
        if sources and RAG_ENABLED:
            response = await langchain_rag.query_with_rag(query, sources=sources, top_k=top_k)
        else:
            response = await langchain_rag.query_without_rag(query)
        
        return {
            "success": True,
            "response": response,
            "sources": sources,
            "top_k": top_k,
            "system": "langchain"
        }
    except Exception as e:
        logging.exception("[LangChain RAG] Query failed: %s", e)
        return {"success": False, "message": str(e)}


# Export langchain_rag for use in main app
def get_langchain_rag():
    """Get the initialized LangChain RAG instance"""
    return langchain_rag
