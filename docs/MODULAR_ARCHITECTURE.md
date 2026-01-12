# Modular Architecture Guide

## 🏗️ Architecture Overview

The application has been refactored into a **modular, scalable architecture** with sub-applications:

```
app.py (Main Server/Orchestrator)
├── common/          → Shared APIs (health, models, system switching)
├── app_manual/      → Manual RAG implementation with endpoints
├── app_langchain/   → LangChain RAG implementation with endpoints
└── static/          → Frontend (HTML/JS/CSS)
```

## 📦 Module Structure

### **Main Server (`app.py`)**
- **Role**: Orchestrator that coordinates all sub-apps
- **Responsibilities**:
  - WebSocket communication (`/ws`)
  - Static file serving (`/static`)
  - Unified file upload (`/api/rag/ingest_file`)
  - Aggregated stats (`/api/rag/stats`)
  - Legacy endpoints for backward compatibility

### **Common Module (`common/app.py`)**
- **Prefix**: None (root level)
- **Tag**: `common`
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /api/models` - List available models
  - `POST /api/models/load` - Load a specific model
  - `POST /api/system/switch` - Switch between manual/langchain
  - `GET /api/system/current` - Get current system

### **Manual RAG Module (`app_manual/app.py`)**
- **Prefix**: `/api/rag/manual`
- **Tag**: `manual-rag`
- **Endpoints**:
  - `GET /api/rag/manual/stats` - Get manual RAG stats
  - `POST /api/rag/manual/ingest_text` - Ingest text
  - `POST /api/rag/manual/ingest_file` - Ingest file
  - `POST /api/rag/manual/preview` - Preview RAG context

### **LangChain RAG Module (`app_langchain/app.py`)**
- **Prefix**: `/api/rag/langchain`
- **Tag**: `langchain-rag`
- **Endpoints**:
  - `GET /api/rag/langchain/stats` - Get LangChain RAG stats
  - `POST /api/rag/langchain/ingest_text` - Ingest text
  - `POST /api/rag/langchain/ingest_file` - Ingest file
  - `POST /api/rag/langchain/query` - Direct query to LangChain

## 🔌 API Endpoint Listing

### **Common Endpoints**
```
GET  /health                    - Health check
GET  /api/models                - List available models
POST /api/models/load           - Load a specific model
POST /api/system/switch         - Switch between systems
GET  /api/system/current        - Get current system
```

### **Manual RAG Endpoints**
```
GET  /api/rag/manual/stats      - Manual system stats
POST /api/rag/manual/ingest_text - Ingest text into manual system
POST /api/rag/manual/ingest_file - Ingest file into manual system
POST /api/rag/manual/preview    - Preview manual RAG context
```

### **LangChain RAG Endpoints**
```
GET  /api/rag/langchain/stats   - LangChain system stats
POST /api/rag/langchain/ingest_text - Ingest text into LangChain
POST /api/rag/langchain/ingest_file - Ingest file into LangChain
POST /api/rag/langchain/query   - Direct query to LangChain
```

### **Unified/Legacy Endpoints**
```
GET  /                          - Main HTML page
GET  /api/rag/stats             - Aggregated stats from both systems
POST /api/rag/ingest_file       - Upload file to BOTH systems
POST /api/rag/ingest_text       - Ingest text to BOTH systems
POST /api/rag/preview           - Preview context (manual system)
```

### **WebSocket**
```
WS   /ws                        - WebSocket for real-time chat
```

## 🎯 Benefits of Modular Architecture

### 1. **Separation of Concerns**
- Each module has a clear, single responsibility
- Common code (health, models) isolated in `common/`
- RAG implementations completely separated

### 2. **Scalability**
- Easy to add new modules (e.g., `app_llamaindex/`, `app_chroma/`)
- Each module can be developed independently
- No code duplication between modules

### 3. **Testability**
- Each module can be tested in isolation
- Mock dependencies easily
- Unit tests per module

### 4. **Discoverability**
- All endpoints visible in OpenAPI docs at `/docs`
- Clear URL structure with prefixes
- Tags organize endpoints by module

### 5. **Maintainability**
- Changes to one module don't affect others
- Clear file organization
- Easy to locate code for specific features

### 6. **Single Port Architecture**
- All modules accessible through port `8081`
- No need for complex service mesh
- Simple deployment

## 🔄 How to Add a New Module

### Example: Adding a ChromaDB RAG System

1. **Create directory and router:**
```bash
mkdir app_chromadb
touch app_chromadb/__init__.py
touch app_chromadb/app.py
touch app_chromadb/chroma_rag.py
```

2. **Create router in `app_chromadb/app.py`:**
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/rag/chromadb", tags=["chroma-rag"])

@router.get("/stats")
async def chromadb_stats():
    return {"system": "chromadb", "status": "active"}

@router.post("/ingest_file")
async def chromadb_ingest(file):
    # Implementation
    pass
```

3. **Register in main `app.py`:**
```python
from app_chromadb.app import router as chromadb_router

app.include_router(chromadb_router)
```

4. **Update Dockerfile:**
```dockerfile
COPY ../app_chromadb/ ./app_chromadb/
```

5. **Rebuild and restart:**
```bash
docker compose build fastapi
docker compose up -d
```

**New endpoints automatically available:**
- `GET /api/rag/chromadb/stats`
- `POST /api/rag/chromadb/ingest_file`

## 📊 Testing

### Test All Endpoints
```bash
# Health
curl http://localhost:8081/health

# Common
curl http://localhost:8081/api/models
curl http://localhost:8081/api/system/current

# Manual RAG
curl http://localhost:8081/api/rag/manual/stats

# LangChain RAG
curl http://localhost:8081/api/rag/langchain/stats

# Unified
curl http://localhost:8081/api/rag/stats
```

### View OpenAPI Documentation
- **Swagger UI**: http://localhost:8081/docs
- **ReDoc**: http://localhost:8081/redoc
- **OpenAPI JSON**: http://localhost:8081/openapi.json

### List All Endpoints
```bash
curl -s http://localhost:8081/openapi.json | \
  python3 -c "import sys, json; \
  data = json.load(sys.stdin); \
  print('\\n'.join([f'{method.upper()} {path}' for path, methods in data['paths'].items() for method in methods.keys()]))"
```

## 🔑 Key Design Decisions

### 1. **APIRouter vs Sub-Applications**
- Used `APIRouter` instead of `FastAPI()` instances
- Routers are lightweight and share middleware
- Better performance than mounting sub-apps with `app.mount()`

### 2. **Shared RAG Store Access**
- Main server gets instances via `get_rag_store()` and `get_langchain_rag()`
- Single instance per system (singleton pattern)
- Shared between WebSocket and HTTP endpoints

### 3. **Backward Compatibility**
- Kept legacy endpoints in main `app.py`
- Unified `/api/rag/ingest_file` indexes in BOTH systems
- Frontend doesn't need changes

### 4. **URL Structure**
- Module-specific: `/api/rag/{module}/{action}`
- Common endpoints: `/api/{resource}`
- Unified endpoints: `/api/rag/{action}` (backward compatible)

### 5. **Logging Prefixes**
- Each module logs with prefix: `[Manual RAG]`, `[LangChain RAG]`, `[Common]`, `[Server]`
- Easy to trace which module handled request

## 🚀 Future Enhancements

### Potential New Modules

1. **`app_agents/`** - AI agents with function calling
2. **`app_memory/`** - Conversation memory with SQLite
3. **`app_llamaindex/`** - LlamaIndex RAG system
4. **`app_chroma/`** - ChromaDB vector store
5. **`app_pinecone/`** - Pinecone cloud vector DB
6. **`app_streaming/`** - Server-sent events for streaming
7. **`app_auth/`** - Authentication and authorization
8. **`app_analytics/`** - Usage analytics and metrics

### Architecture Evolution

```
Current: Single FastAPI app with routers
└── Best for: Small to medium applications

Future: Microservices (if needed)
├── Gateway: NGINX/Traefik
├── Service 1: Manual RAG (port 8001)
├── Service 2: LangChain RAG (port 8002)
├── Service 3: Common APIs (port 8003)
└── Message Queue: RabbitMQ/Redis

Future: Kubernetes (if needed)
├── Deployment: fastapi-server
├── Deployment: ollama
├── Deployment: vector-db
└── Service: load-balancer
```

## 📝 Migration Notes

### What Changed

**Before:**
- Everything in single `app.py` (479 lines)
- No clear separation between systems
- Hard to test individual components

**After:**
- Main server: `app.py` (420 lines)
- Common module: `common/app.py` (140 lines)
- Manual RAG: `app_manual/app.py` (180 lines)
- LangChain RAG: `app_langchain/app.py` (180 lines)
- Total: Well-organized, testable modules

### Backward Compatibility
✅ All existing frontend code works without changes
✅ Legacy endpoints maintained
✅ WebSocket behavior unchanged
✅ File upload indexes in BOTH systems

### Breaking Changes
❌ None - fully backward compatible!

## 🎓 Learning Resources

### FastAPI Documentation
- [Sub Applications](https://fastapi.tiangolo.com/advanced/sub-applications/)
- [APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Architecture Patterns
- [Microservices Pattern](https://microservices.io/)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)
- [Modular Monolith](https://www.kamilgrzybek.com/design/modular-monolith-primer/)

## ✅ Verification

**Test Results:**
- ✅ Health endpoint working
- ✅ All 19 endpoints registered
- ✅ Manual RAG stats: 11 chunks
- ✅ LangChain RAG stats: 0 chunks (fresh)
- ✅ Common endpoints working
- ✅ Module-specific endpoints working
- ✅ WebSocket connections working
- ✅ Frontend loads successfully
- ✅ OpenAPI docs accessible at `/docs`

**Architecture Status:** ✅ **PRODUCTION READY**

---

**Version:** 2.0.0  
**Architecture:** Modular with Sub-Apps  
**Deployment:** Docker Compose  
**Port:** 8081 (single port for all modules)
