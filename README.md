# 🚀 WebSocket Chat with Ollama - Modular Architecture

A production-ready, modular chat application with dual RAG (Retrieval-Augmented Generation) systems, real-time WebSocket communication, and multiple LLM support.

## ✨ Key Features

- 🏗️ **Modular Architecture**: Scalable sub-app design with clear separation of concerns
- 🔄 **Dual RAG Systems**: Compare Manual vs LangChain implementations side-by-side
- 🧠 **ChromaDB Support**: Persistent vector store option alongside FAISS
- 🤖 **AI Agents**: ReAct agent with function calling, tool use, and reasoning (NEW!)
- 🤖 **Multiple AI Models**: Gemma 2B, Phi-3, Llama 3.2, Qwen 2.5
- 📁 **Document Upload**: PDF, DOCX, TXT, Markdown support
- 🔌 **Single Port**: All endpoints accessible through one port (8081)
- 🐳 **Fully Dockerized**: Complete containerized setup with Docker Compose
- ⚡ **Real-time Communication**: WebSocket-based chat for instant messaging
- 📊 **OpenAPI Documentation**: Auto-generated API docs at `/docs`
- 🎨 **Modern UI**: Clean, responsive chat interface with system toggle

## 🏗️ Architecture

### Modular Structure
```
app.py (Main Server/Orchestrator)
├── common/          → Shared APIs (health, models, system switching)
├── app_manual/      → Manual RAG implementation
├── app_langchain/   → LangChain RAG implementation
├── app_agents/      → AI Agent system with ReAct pattern (NEW!)
└── static/          → Frontend (HTML/JS/CSS)
```

### Benefits
- ✅ **Scalable**: Easy to add new modules (ChromaDB, LlamaIndex, etc.)
- ✅ **Testable**: Each module can be tested independently
- ✅ **Maintainable**: Clear code organization and separation
- ✅ **Discoverable**: All endpoints auto-documented
- ✅ **Backward Compatible**: Legacy endpoints preserved

## 📦 Project Structure

```
websockets/
├── app.py                           # Main orchestrator server
├── app_old_backup.py                # Backup of previous monolithic version
├── requirements.txt                 # Python dependencies
├── task                             # Task/project notes
├── MODULAR_QUICK_REF.md            # Quick reference guide
│
├── common/                          # Shared APIs module
│   ├── __init__.py
│   └── app.py                       # Health, models, system switching
│
├── app_manual/                      # Manual RAG module
│   ├── __init__.py
│   ├── app.py                       # Manual RAG router
│   └── rag_store.py                 # Custom RAG implementation
│
├── app_langchain/                   # LangChain RAG module
│   ├── __init__.py
│   ├── app.py                       # LangChain RAG router
│   └── langchain_rag.py             # LangChain implementation
│app_agents/                      # AI Agent module (NEW!)
│   ├── __init__.py
│   ├── app.py                       # Agent API router
│   ├── agent1.py                    # ReAct agent implementation
│   └── tools.py                     # Tool definitions (calculator, time, weather, etc.)
│
├── 
├── builds/                          # Docker configuration
│   ├── Dockerfile                   # FastAPI container
│   ├── docker-compose.yml           # Multi-container orchestration
│   ├── pull-model.sh               # Script to pull Ollama models
│   ├── pull-all-models.sh          # Pull all supported models
│   └── verify.sh                   # Verify setup
│
├── data/                            # Data directory (gitignored)
│   ├── rag_store.json              # Manual RAG storage
│   ├── AGENT1_GUIDE.md             # AI Agent learning guide (NEW!)
│   ├── MODULAR_ARCHITECTURE.md     # Architecture deep dive
│   ├── CHAT_FLOW.md                # Communication flow
│   ├── DUAL_SYSTEM_GUIDE.md        # Dual RAG comparison
│   ├── MODEL_SELECTION.md          # Model information
│   ├── QUICK_REFERENCE.md          # Quick commands
│   ├── PROJECT_SUMMARY.md          # Project summary
│   ├── future_scope.md             # Future enhancements
│   └── understand_rag_without_code.md  # RAG explanation
│
└── static/                          # Frontend assets
    ├── index.html                  # Chat interface
    ├── agent1.html                 # Agent1 demo UI (NEW!)
│   ├── PROJECT_SUMMARY.md          # Project summary
│   ├── future_scope.md             # Future enhancements
│   └── understand_rag_without_code.md  # RAG explanation
│
└── static/                          # Frontend assets
    ├── index.html                  # Chat interface
    ├── script.js                   # WebSocket client
    ├── style.css                   # Styling
    └── test.html                   # Test page
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ free RAM
- Internet connection for initial setup

### 1. Navigate to project
```bash
cd /Users/shivam/Desktop/workspace/poc/websockets
```

### 2. Start services
```bash
cd builds/
docker compose up -d
```

### 3. Wait for models to load
```bash
# Check logs
docker compose logs -f

# Verify models loaded
docker exec ollama ollama list
```

### 4. Access application
- **Frontend**: http://localhost:8081
- **Agent1 UI**: http://localhost:8081/agents/agent1 (NEW!)
- **API Docs**: http://localhost:8081/docs
- **Health Check**: http://localhost:8081/health

### Enable ChromaDB (Optional)
```bash
# in project root
echo 'RAG_VECTORSTORE=chroma' >> .env
echo 'RAG_VECTORSTORE_PATH=/app/data/chroma_db' >> .env
cd builds && docker compose up -d --build
```

## 📡 API Endpoints (19 Total)

### Common Endpoints
```
GET  /health                     - Health check
GET  /api/models                 - List available models
POST /api/models/load            - Load specific model
POST /api/system/switch          - Switch between systems
GET  /api/system/current         - Get current system
```

### Manual RAG Module
```
GET  /api/rag/manual/stats       - Manual RAG stats
POST /api/rag/manual/ingest_text - Ingest text
POST /api/rag/manual/ingest_file - Ingest file
POST /api/rag/manual/preview     - Preview context
```

### LangChain RAG Module
```
GET  /api/rag/langchain/stats    - LangChain stats
POST /api/rag/langchain/ingest_text - Ingest text
POST /api/rag/langchain/ingest_file - Ingest file
POST /api/rag/langchain/query    - Direct query
```

Chroma vs FAISS (LangChain):
- Set `RAG_VECTORSTORE=faiss|chroma` (env overrides YAML config)
- For Chroma, set `RAG_VECTORSTORE_PATH=/app/data/chroma_db` (mapped to `data/` on host)

### Unified Endpoints
```
GET  /                           - Main HTML page
GET  /agents/agent1              - Agent1 demo UI (NEW!)
WS   /ws                         - WebSocket chat
GET  /api/rag/stats              - Aggregated stats
POST /api/rag/ingest_file        - Upload to both systems
POST /api/rag/ingest_text        - Ingest to both systems
POST /api/rag/preview            - Preview context
```

### Agent Endpoints (NEW!)
```
GET  /api/agents/agent1/info     - Agent metadata & capabilities
GET  /api/agents/agent1/tools    - List available tools
POST /api/agents/agent1/query    - Query agent with message
POST /api/agents/agent1/reset    - Reset conversation history
```

## 🧪 Testing

### List all endpoints
```bash
curl -s http://localhost:8081/openapi.json | \
  python3 -c "import sys, json; \
  data = json.load(sys.stdin); \
  print('\\n'.join([f'{method.upper()} {path}' \
  for path, methods in data['paths'].items() \
  for method in methods.keys()]))"
```

### Test health
```bash
curl http://localhost:8081/health | python3 -m json.tool
```

### Test stats
```bash
# Unified stats (both systems)
curl http://localhost:8081/api/rag/stats | python3 -m json.tool

# Manual system only
curl http://localhost:8081/api/rag/manual/stats | python3 -m json.tool

# LangChain system only
curl http://localhost:8081/api/rag/langchain/stats | python3 -m json.tool
```

## ⚙️ Configuration

- Config files live in [config/langchain.yaml](config/langchain.yaml) and [config/manual.yaml](config/manual.yaml).
- At runtime, settings are loaded from YAML and merged with environment variables via [common/config.py](common/config.py).
- Precedence: environment variables override YAML, which override code defaults.
- To make YAML configs available inside the FastAPI container, add this volume to the `fastapi` service in [builds/docker-compose.yml](builds/docker-compose.yml):
    - `../config:/app/config`

Key settings (LangChain):
- `vectorstore`: `faiss` or `chroma` (default `faiss`)
- `vectorstore_path`: persistent path for Chroma (e.g., `/app/data/chroma_db`)
- `chunk_size`, `chunk_overlap`: text chunking for embeddings
- `rag_enabled`, `rag_top_k`, `save_uploads`, `upload_dir`

Switching vector stores:
- Set `RAG_VECTORSTORE=faiss|chroma` in `.env` (env takes priority over YAML).
- For Chroma, also set `RAG_VECTORSTORE_PATH=/app/data/chroma_db`.

### ChromaDB Test Suite
Run the comprehensive test (auto-detects port, defaults to 8081):
```bash
python tests/test_chroma.py
```
Flags:
- `--base-url http://localhost:8081` to override target
- `--timeout 60` to extend request timeout
- `--skip-persistence` to skip the manual restart step

## 🔧 Development

### Rebuild after changes
```bash
cd builds/
docker compose build fastapi
docker compose up -d
```

### View logs
```bash
cd builds/
docker compose logs -f fastapi      # Follow logs
docker compose logs --tail=50       # Last 50 lines
```

### Stop services
```bash
cd builds/
docker compose down
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [MODULAR_ARCHITECTURE.md](docs/architecture/MODULAR_ARCHITECTURE.md) | Deep dive into modular design |
| [MODULAR_QUICK_REF.md](MODULAR_QUICK_REF.md) | Quick reference card |
| [SETUP.md](docs/setup/SETUP.md) | Detailed setup instructions |
| [CHAT_FLOW.md](docs/flows/CHAT_FLOW.md) | WebSocket communication flow |
| [DUAL_SYSTEM_GUIDE.md](docs/guides/DUAL_SYSTEM_GUIDE.md) | Manual vs LangChain comparison |
| [MODEL_SELECTION.md](docs/reference/MODEL_SELECTION.md) | Model information and selection |
| [future_scope.md](docs/roadmap/future_scope.md) | Planned features and enhancements |

## 🎯 Adding a New Module

Example: Adding ChromaDB support

1. **Create module directory:**
```bash
mkdir app_chromadb
touch app_chromadb/__init__.py
touch app_chromadb/app.py
```

2. **Create router:**
```python
# app_chromadb/app.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/rag/chromadb", tags=["chroma-rag"])

@router.get("/stats")
async def chromadb_stats():
    return {"system": "chromadb", "status": "active"}
```

3. **Register in main app:**
```python
# app.py
from app_chromadb.app import router as chromadb_router
app.include_router(chromadb_router)
```

4. **Update Dockerfile:**
```dockerfile
COPY ../app_chromadb/ ./app_chromadb/
```

5. **Rebuild:**
```bash
cd builds/
docker compose build fastapi && docker compose up -d
```

6. **Test:**
```bash
curl http://localhost:8081/api/rag/chromadb/stats
```

**New endpoint automatically available at `/docs`!**

## 🔬 Technology Stack

- **Backend**: FastAPI 0.109.0, Uvicorn
- **AI**: Ollama (Gemma 2B, Phi-3, Llama 3.2, Qwen 2.5)
- **Embeddings**: nomic-embed-text
- **RAG (Manual)**: NumPy, custom cosine similarity
- **RAG (LangChain)**: LangChain, FAISS/Chroma, RecursiveCharacterTextSplitter
- **File Parsing**: pypdf (PDF), python-docx (DOCX)
- **Containerization**: Docker, Docker Compose
- **Frontend**: Vanilla JavaScript, WebSocket API

## 📊 Current Status

- ✅ Modular architecture implemented
- ✅ 19 endpoints registered
- ✅ All modules operational
- ✅ Both RAG systems working
- ✅ WebSocket communication active
- ✅ OpenAPI documentation available
- ✅ Production ready

## 🚀 Future Enhancements

See [future_scope.md](docs/future_scope.md) for detailed roadmap:

1. **AI Agents** - Function calling, tool integration
2. **Memory System** - Conversation history, session management
3. **Advanced RAG** - Hybrid search, reranking, citations
4. **Streaming** - Server-sent events for token streaming
5. **Multi-Agent** - Coordinated agent systems

## 🤝 Contributing

This is a POC project. To extend:

1. Create a new module directory
2. Implement router with endpoints
3. Register in main `app.py`
4. Update Dockerfile
5. Rebuild and test

## 📄 License

This is a proof-of-concept project for learning purposes.

## 🙏 Acknowledgments

- Ollama for local LLM inference
- LangChain for RAG framework
- FastAPI for modern Python web framework
- All open-source contributors

---

**Version**: 2.0.0 - Modular Architecture  
**Status**: ✅ Production Ready  
**Port**: 8081 (single port for all services)  
**Architecture**: Modular with Sub-Apps  
**Date**: January 2026
