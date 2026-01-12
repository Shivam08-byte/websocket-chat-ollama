"""
Unified RAG router for backward compatibility
Provides endpoints that work with BOTH Manual and LangChain systems
"""

import os
import logging
from fastapi import APIRouter, UploadFile, File

from .file_parser import parse_file, save_upload

# Create router for unified RAG endpoints
router = APIRouter(prefix="/api/rag", tags=["unified-rag"])

# Configuration
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_CHARS = int(os.getenv("RAG_MAX_CHARS", "2000"))
RAG_SAVE_UPLOADS = os.getenv("RAG_SAVE_UPLOADS", "true").lower() in {"1", "true", "yes", "on"}
RAG_UPLOAD_DIR = os.getenv("RAG_UPLOAD_DIR", "/app/data/uploads")

logging.basicConfig(level=logging.INFO)

# Will be set by main app
_rag_store = None
_langchain_rag = None


def init_unified_rag(rag_store, langchain_rag):
    """Initialize unified RAG with both systems"""
    global _rag_store, _langchain_rag
    _rag_store = rag_store
    _langchain_rag = langchain_rag
    logging.info("[Unified RAG] Initialized with both systems")


@router.get("/stats")
async def unified_stats():
    """Get aggregated stats from both RAG systems"""
    manual_stats = {"enabled": RAG_ENABLED, **_rag_store.stats()}
    langchain_stats = _langchain_rag.stats()
    
    return {
        "manual": manual_stats,
        "langchain": langchain_stats,
        "architecture": "modular"
    }


@router.post("/ingest_text")
async def unified_ingest_text(payload: dict):
    """
    Ingest text into BOTH RAG systems
    Maintains backward compatibility with legacy frontend
    """
    text = payload.get("text", "")
    source = payload.get("source", "uploaded")
    
    if not text.strip():
        return {"success": False, "message": "No text provided"}
    
    try:
        added_manual = await _rag_store.add_text(text, source=source)
        added_langchain = _langchain_rag.add_documents(text, source=source)
        
        return {
            "success": True, 
            "added_chunks": added_manual,
            "added_chunks_langchain": added_langchain,
            "source": source
        }
    except Exception as e:
        logging.exception(f"[Unified RAG] Ingest text failed: {e}")
        return {"success": False, "message": str(e)}


@router.post("/ingest_file")
async def unified_ingest_file(file: UploadFile = File(...)):
    """
    Ingest file into BOTH RAG systems
    Maintains backward compatibility with existing frontend
    
    Supports: PDF, DOCX, TXT, Markdown
    """
    try:
        content = await file.read()
        filename = file.filename or "uploaded"
        
        logging.info(
            "[Unified RAG] File upload received | filename=%s | bytes=%s", 
            filename, len(content) if content else 0
        )
        
        # Save original file to disk
        if RAG_SAVE_UPLOADS and filename:
            save_upload(content, filename, RAG_UPLOAD_DIR)
        
        # Parse file content
        success, text, error_msg = parse_file(content, filename)
        
        if not success:
            return {"success": False, "message": error_msg}
        
        # Index in BOTH systems
        added_manual = await _rag_store.add_text(text, source=filename)
        added_langchain = _langchain_rag.add_documents(text, source=filename)
        
        logging.info(
            "[Unified RAG] Indexed in BOTH systems | filename=%s | manual=%s | langchain=%s", 
            filename, added_manual, added_langchain
        )
        
        if added_manual <= 0 and added_langchain <= 0:
            return {
                "success": False, 
                "message": "No chunks indexed (file may be empty or unsupported)"
            }
        
        return {
            "success": True, 
            "added_chunks": added_manual,
            "added_chunks_langchain": added_langchain,
            "source": filename
        }
        
    except Exception as e:
        logging.exception(f"[Unified RAG] File upload failed: {e}")
        return {"success": False, "message": str(e)}


@router.post("/preview")
async def unified_preview(payload: dict):
    """
    Preview retrieved context for a query
    Uses manual RAG system for preview
    """
    try:
        query = payload.get("query", "").strip()
        sources = payload.get("sources")
        top_k = int(payload.get("top_k", RAG_TOP_K))
        
        if not query:
            return {"success": False, "message": "No query provided"}
        
        # Clean sources
        if sources and isinstance(sources, list):
            sources = [str(s) for s in sources]
        else:
            sources = None
        
        # Build context using manual system
        ctx = await _rag_store.build_context(
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
        logging.exception(f"[Unified RAG] Preview failed: {e}")
        return {"success": False, "message": str(e)}
