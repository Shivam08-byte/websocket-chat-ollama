# 🚀 Modular Architecture Quick Reference

## Directory Structure
```
websockets/
├── app.py (79 lines)         # Clean orchestrator - 80% smaller!
├── common/
│   ├── __init__.py
│   ├── app.py               # Common APIs (health, models, system)
│   ├── file_parser.py       # Document parsing (PDF, DOCX, TXT)
│   ├── query_service.py     # Query routing between RAG systems
│   ├── websocket_handler.py # WebSocket management
│   └── unified_rag.py       # Unified endpoints (both systems)
├── app_manual/
│   ├── __init__.py
│   ├── app.py               # Manual RAG router
│   └── rag_store.py         # Manual RAG implementation
├── app_langchain/
│   ├── __init__.py
│   ├── app.py               # LangChain RAG router
│   └── langchain_rag.py     # LangChain RAG implementation
├── builds/
│   ├── Dockerfile           # Updated for modular structure
│   └── docker-compose.yml
├── docs/
│   ├── MODULAR_ARCHITECTURE.md  # Full documentation
│   └── CLEAN_ARCHITECTURE.md    # Refactoring details
└── static/
    ├── index.html
    ├── script.js
    └── style.css
```

## API Endpoints by Module

### Common (`common/app.py`)
- `GET /health`
- `GET /api/models`
- `POST /api/models/load`
- `POST /api/system/switch`
- `GET /api/system/current`

### Manual RAG (`app_manual/app.py`)
- `GET /api/rag/manual/stats`
- `POST /api/rag/manual/ingest_text`
- `POST /api/rag/manual/ingest_file`
- `POST /api/rag/manual/preview`

### LangChain RAG (`app_langchain/app.py`)
- `GET /api/rag/langchain/stats`
- `POST /api/rag/langchain/ingest_text`
- `POST /api/rag/langchain/ingest_file`
- `POST /api/rag/langchain/query`

### Main Server (`app.py`)
- `GET /` - Frontend
- `WS /ws` - WebSocket
- `GET /api/rag/stats` - Unified stats
- `POST /api/rag/ingest_file` - Upload to both systems
- `POST /api/rag/ingest_text` - Ingest to both systems
- `POST /api/rag/preview` - Preview context

## Quick Commands

### Start/Stop
```bash
cd builds/
docker compose up -d      # Start
docker compose down       # Stop
docker compose restart    # Restart
```

### Rebuild After Changes
```bash
cd builds/
docker compose build fastapi
docker compose up -d
```

### View Logs
```bash
cd builds/
docker compose logs -f fastapi    # Follow logs
docker compose logs --tail=50     # Last 50 lines
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8081/health

# All endpoints list
curl -s http://localhost:8081/openapi.json | python3 -c "import sys, json; data = json.load(sys.stdin); print('\\n'.join([f'{method.upper()} {path}' for path, methods in data['paths'].items() for method in methods.keys()]))"

# Manual RAG stats
curl http://localhost:8081/api/rag/manual/stats

# LangChain RAG stats
curl http://localhost:8081/api/rag/langchain/stats

# Unified stats
curl http://localhost:8081/api/rag/stats
```

## Adding a New Module

1. **Create directory:**
```bash
mkdir app_newmodule
touch app_newmodule/__init__.py
touch app_newmodule/app.py
```

2. **Create router in `app_newmodule/app.py`:**
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/newmodule", tags=["newmodule"])

@router.get("/status")
async def status():
    return {"status": "active"}
```

3. **Register in `app.py`:**
```python
from app_newmodule.app import router as newmodule_router
app.include_router(newmodule_router)
```

4. **Update `builds/Dockerfile`:**
```dockerfile
COPY ../app_newmodule/ ./app_newmodule/
```

5. **Rebuild:**
```bash
cd builds/
docker compose build fastapi
docker compose up -d
```

6. **Test:**
```bash
curl http://localhost:8081/api/newmodule/status
```

## URL Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| `/api/{module}/*` | Module-specific | `/api/rag/manual/stats` |
| `/api/{resource}` | Common resources | `/api/models` |
| `/{path}` | Main server | `/health`, `/` |

## Benefits

✅ **Single Port** - All modules on port 8081  
✅ **Scalable** - Easy to add new modules  
✅ **Testable** - Each module isolated  
✅ **Discoverable** - Auto-generated docs at `/docs`  
✅ **Maintainable** - Clear separation of concerns  
✅ **Backward Compatible** - Old endpoints still work  

## OpenAPI Documentation

- **Swagger UI**: http://localhost:8081/docs
- **ReDoc**: http://localhost:8081/redoc
- **JSON Schema**: http://localhost:8081/openapi.json

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main orchestrator, WebSocket, unified endpoints |
| `common/app.py` | Health, models, system switching |
| `app_manual/app.py` | Manual RAG endpoints |
| `app_manual/rag_store.py` | Manual RAG implementation |
| `app_langchain/app.py` | LangChain RAG endpoints |
| `app_langchain/langchain_rag.py` | LangChain implementation |
| `builds/Dockerfile` | Container definition |
| `builds/docker-compose.yml` | Multi-container setup |

## Logging Prefixes

| Prefix | Module |
|--------|--------|
| `[Server]` | Main app.py |
| `[Common]` | common/app.py |
| `[Manual RAG]` | app_manual/app.py |
| `[LangChain RAG]` | app_langchain/app.py |

## Environment Variables

All modules use the same environment variables from `docker-compose.yml`:
- `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `OLLAMA_EMBED_MODEL`
- `RAG_ENABLED`
- `RAG_TOP_K`
- `RAG_MAX_CHARS`
- `RAG_STORE_PATH`
- `RAG_UPLOAD_DIR`

## Status Check

```bash
# Container status
cd builds/ && docker compose ps

# Health check
curl -s http://localhost:8081/health | python3 -m json.tool

# All endpoints
curl -s http://localhost:8081/openapi.json | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Total endpoints: {len(data['paths'])}\")"

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
```

## Migration Notes

**No Breaking Changes!**
- ✅ Frontend works without modifications
- ✅ WebSocket behavior unchanged
- ✅ Legacy endpoints maintained
- ✅ File uploads index in both systems
- ✅ All existing functionality preserved

---

**Version:** 2.1.0 - Clean Modular Architecture  
**Date:** January 2026  
**Status:** ✅ Production Ready  
**Refactoring:** app.py reduced from 411 → 79 lines (80% smaller!)
