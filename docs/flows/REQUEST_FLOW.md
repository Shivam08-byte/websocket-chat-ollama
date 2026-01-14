# Request Flow in Modular Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
│                    (Browser/Frontend)                        │
│                     localhost:8081                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP/WebSocket
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    Main Server (app.py)                      │
│                     FastAPI App                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  WebSocket Handler (/ws)                           │    │
│  │  - Manages connections                             │    │
│  │  - Routes to Manual or LangChain                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Unified Endpoints                                 │    │
│  │  - GET /                                           │    │
│  │  - GET /api/rag/stats                             │    │
│  │  - POST /api/rag/ingest_file (indexes in BOTH)    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌───────────┬──────────────┬────────────────────────┐    │
│  │           │              │                         │    │
│  │  Router   │   Router     │    Router               │    │
│  │  Include  │   Include    │    Include              │    │
│  └───────────┴──────────────┴────────────────────────┘    │
│       │            │                  │                     │
└───────┼────────────┼──────────────────┼─────────────────────┘
        │            │                  │
        │            │                  │
┌───────▼──────┐ ┌──▼──────────┐ ┌────▼───────────────┐
│   common/    │ │ app_manual/  │ │  app_langchain/    │
│    app.py    │ │   app.py     │ │     app.py         │
│              │ │              │ │                    │
│  APIRouter   │ │  APIRouter   │ │   APIRouter        │
│  prefix=""   │ │  prefix=     │ │   prefix=          │
│              │ │  "/api/rag/  │ │   "/api/rag/       │
│  ┌─────────┐ │ │   manual"    │ │    langchain"      │
│  │/health  │ │ │              │ │                    │
│  │/api/    │ │ │  ┌─────────┐ │ │  ┌──────────┐     │
│  │ models  │ │ │  │/stats   │ │ │  │/stats    │     │
│  │/api/    │ │ │  │/ingest_ │ │ │  │/ingest_  │     │
│  │ system  │ │ │  │  text   │ │ │  │  text    │     │
│  └─────────┘ │ │  │/ingest_ │ │ │  │/ingest_  │     │
│              │ │  │  file   │ │ │  │  file    │     │
│              │ │  │/preview │ │ │  │/query    │     │
│              │ │  └─────────┘ │ │  └──────────┘     │
│              │ │       │      │ │       │            │
│              │ │       ▼      │ │       ▼            │
│              │ │  rag_store.py│ │  langchain_rag.py  │
│              │ │  (NumPy,JSON)│ │  (FAISS,LC)        │
└──────────────┘ └──────────────┘ └────────────────────┘
```

## Request Flow Examples

### 1. Health Check Request

```
Client: GET /health
    │
    ▼
Main Server (app.py)
    │
    ▼
Common Router (common/app.py)
    │
    └─> @router.get("/health")
        └─> Return: {"status": "healthy", ...}
```

### 2. Manual RAG Stats Request

```
Client: GET /api/rag/manual/stats
    │
    ▼
Main Server (app.py)
    │
    ▼
Manual RAG Router (app_manual/app.py)
    │
    ├─> Prefix: /api/rag/manual
    │
    └─> @router.get("/stats")  # Full path: /api/rag/manual/stats
        │
        ▼
    rag_store.stats()  # From rag_store.py
        │
        └─> Return: {"chunks": 11, "sources": {...}}
```

### 3. LangChain File Upload

```
Client: POST /api/rag/langchain/ingest_file
    │
    ▼
Main Server (app.py)
    │
    ▼
LangChain Router (app_langchain/app.py)
    │
    ├─> Prefix: /api/rag/langchain
    │
    └─> @router.post("/ingest_file")
        │
        ├─> Parse file (PDF/DOCX/TXT)
        │
        ▼
    langchain_rag.add_documents()  # From langchain_rag.py
        │
        ├─> Chunk text (RecursiveCharacterTextSplitter)
        ├─> Generate embeddings (OllamaEmbeddings)
        └─> Store in FAISS vectorstore
        │
        └─> Return: {"success": true, "added_chunks": 5}
```

### 4. Unified File Upload (Both Systems)

```
Client: POST /api/rag/ingest_file
    │
    ▼
Main Server (app.py)
    │
    └─> @app.post("/api/rag/ingest_file")  # Main server handles this
        │
        ├─> Parse file once
        │
        ├───────────────┬───────────────┐
        │               │               │
        ▼               ▼               ▼
    Manual RAG    LangChain RAG    Save to disk
    rag_store     langchain_rag    /app/data/uploads/
    .add_text()   .add_documents()
        │               │
        └───────┬───────┘
                │
                ▼
        Return: {
            "success": true,
            "added_chunks": 6,           # Manual
            "added_chunks_langchain": 5  # LangChain
        }
```

### 5. WebSocket Chat with RAG

```
Client: WS /ws + {"message": "...", "sources": ["doc.pdf"], "useLangchain": true}
    │
    ▼
Main Server (app.py)
    │
    └─> @app.websocket("/ws")
        │
        ├─> Parse message JSON
        ├─> Extract: message, sources, useLangchain
        │
        ├─> if useLangchain == true:
        │   │
        │   └─> query_ollama(..., use_langchain=True)
        │       │
        │       └─> langchain_rag.query_with_rag()
        │           │
        │           ├─> FAISS vector search
        │           ├─> Retrieve top_k chunks
        │           ├─> Build prompt with context
        │           └─> Query Ollama LLM
        │
        ├─> else:  # Manual system
        │   │
        │   └─> query_ollama(..., use_langchain=False)
        │       │
        │       └─> rag_store.build_context()
        │           │
        │           ├─> Get embeddings from Ollama
        │           ├─> NumPy cosine similarity
        │           ├─> Retrieve top_k chunks
        │           ├─> Build prompt with context
        │           └─> Query Ollama LLM
        │
        └─> Send response via WebSocket
```

## URL Routing Resolution

### How FastAPI Resolves URLs

```python
# Main app.py
app = FastAPI()

# Register routers
app.include_router(common_router)        # prefix=""
app.include_router(manual_router)        # prefix="/api/rag/manual"
app.include_router(langchain_router)     # prefix="/api/rag/langchain"

# Direct routes
@app.get("/")                            # Main page
@app.websocket("/ws")                    # WebSocket
@app.get("/api/rag/stats")              # Unified stats
@app.post("/api/rag/ingest_file")       # Unified upload
```

### Request Matching Priority

1. **Direct routes in main app** (exact match)
   - `/`, `/ws`, `/api/rag/stats`, `/api/rag/ingest_file`

2. **Router with longest prefix match**
   - `/api/rag/langchain/*` → LangChain router
   - `/api/rag/manual/*` → Manual router

3. **Router with no prefix** (common router)
   - `/health`, `/api/models`, `/api/system/*`

### Example URL Resolution

| URL | Matched By | Handler |
|-----|-----------|---------|
| `/` | Main app | `app.get("/")` |
| `/health` | Common router | `common_router.get("/health")` |
| `/api/models` | Common router | `common_router.get("/api/models")` |
| `/api/rag/stats` | Main app | `app.get("/api/rag/stats")` |
| `/api/rag/manual/stats` | Manual router | `manual_router.get("/stats")` |
| `/api/rag/langchain/stats` | LangChain router | `langchain_router.get("/stats")` |
| `/api/rag/ingest_file` | Main app | `app.post("/api/rag/ingest_file")` |
| `/api/rag/manual/ingest_file` | Manual router | `manual_router.post("/ingest_file")` |
| `/api/rag/langchain/ingest_file` | LangChain router | `langchain_router.post("/ingest_file")` |

## Data Flow

### Ollama Container
```
┌─────────────────────────────────┐
│      Ollama Container           │
│      Port: 11434                │
│                                 │
│  ┌──────────────────────────┐  │
│  │  Models                  │  │
│  │  - gemma:2b (LLM)        │  │
│  │  - nomic-embed-text      │  │
│  │    (embeddings)          │  │
│  └──────────────────────────┘  │
│                                 │
│  API Endpoints:                │
│  - POST /api/generate          │
│  - POST /api/embeddings        │
└─────────────────────────────────┘
         ▲
         │ HTTP (internal network)
         │
┌────────┴────────────────────────┐
│   FastAPI Container             │
│   (All modules call Ollama)     │
└─────────────────────────────────┘
```

### Storage

```
data/
├── rag_store.json              # Manual RAG storage
│   └── Format: {
│         "chunks": [...],
│         "metadata": {...}
│       }
│
├── uploads/                    # Original uploaded files
│   ├── doc1.pdf
│   ├── doc2.docx
│   └── doc3.txt
│
└── vectorstore/                # LangChain FAISS vectors (in-memory)
    └── (In memory, not persisted)
```

## Scalability Paths

### Current: Monolithic with Modules (Best for now)
- Single FastAPI app
- Multiple routers (modules)
- Single port (8081)
- Shared resources
- ✅ **Recommended for most use cases**

### Future: True Microservices (If needed)
```
┌──────────────┐
│   Gateway    │ Port 80
│  (NGINX)     │
└───────┬──────┘
        │
    ────┼────────────────────
    │   │       │           │
    ▼   ▼       ▼           ▼
  Port  Port   Port       Port
  8001  8002   8003       8004
  │     │      │          │
Manual  LC   Common    Ollama
 RAG   RAG   APIs      Service
```

### Future: Kubernetes (If needed)
```
┌─────────────────────────────┐
│     Ingress Controller      │
└────────────┬────────────────┘
             │
    ─────────┼──────────────
    │        │             │
    ▼        ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐
│FastAPI │ │Ollama  │ │Vector  │
│Pod x3  │ │Pod x2  │ │DB Pod  │
└────────┘ └────────┘ └────────┘
```

---

**Current Architecture**: Modular Monolith ✅  
**Status**: Production Ready  
**Deployment**: Docker Compose  
**Scaling**: Vertical (more RAM/CPU) or Horizontal (load balancer + multiple containers)
