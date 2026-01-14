## Summary

- ChromaDB integration for LangChain RAG with persistence
- Dynamic data volume and path defaults via `DATA_HOST_DIR` / `DATA_CONTAINER_DIR`
- Env/YAML-configurable `RAG_VECTORSTORE_PATH`, `RAG_UPLOAD_DIR`, and removal of hardcoded `/app/data/*`
- Unified test runner `tests/run_all.sh` with auto-venv and port detection
- New test scripts for common, manual RAG, LangChain RAG, agents, and WebSocket
- Docs reorganization into categorized `docs/` subfolders; root docs moved
- Included `builds/.env` for reproducible container configs

## Motivation

- Provide persistent vector store option (Chroma) alongside FAISS
- Improve portability by deriving defaults from environment variables
- Make testing easier and consistent across environments
- Keep documentation tidy and discoverable in `docs/`

## Changes

- LangChain RAG
  - `app_langchain/langchain_rag.py`: derive `vectorstore_path` from `DATA_CONTAINER_DIR` when not provided; load/persist Chroma
  - `app_langchain/app.py`: default `RAG_VECTORSTORE_PATH`, `RAG_UPLOAD_DIR` based on `DATA_CONTAINER_DIR`
- Manual RAG & common utils
  - `app_manual/app.py`: defaults from `DATA_CONTAINER_DIR`
  - `common/unified_rag.py`: default upload dir uses `DATA_CONTAINER_DIR`
  - `common/file_parser.py`: fallback upload dir from `DATA_CONTAINER_DIR`/`RAG_UPLOAD_DIR`
- Containers
  - `builds/docker-compose.yml`: parameterize data volume `${DATA_HOST_DIR:-../data}:${DATA_CONTAINER_DIR:-/app/data}`
  - `builds/.env`: add `RAG_VECTORSTORE=chroma` and `RAG_VECTORSTORE_PATH=/app/data/chroma_db`
- Tests
  - `tests/test_health.py`, `tests/test_manual_rag.py`, `tests/test_langchain_rag_basic.py`, `tests/test_agents.py`, `tests/test_websocket_chat.py`
  - `tests/run_all.sh`: auto-venv, installs test-only deps (`requests`, `websockets`), detects port, optional compose
- Docs
  - Moved root docs to `docs/` categories and fixed links: `AGENT1_QUICK_REF.md`, `AGENT_IMPLEMENTATION.md`, `CLEANUP_SUMMARY.md`, `MODULAR_QUICK_REF.md`, `DUAL_SYSTEM_GUIDE.md`, `future_scope.md`

## Testing

- Ran `./tests/run_all.sh --skip-persistence`:
  - Common endpoints: OK
  - Manual RAG: stats, ingestion (text/file), preview: OK
  - LangChain RAG: stats, ingestion, query: OK
  - Agents API: info, tools, query, reset: OK
  - WebSocket chat: connect, manual + LangChain messages: OK
  - Chroma suite (no persistence): Passed (some queries may time out intermittently; reruns stable)

## Docs

- See `docs/setup/SETUP.md` for Chroma enablement and configs
- See `docs/reference/MODULAR_QUICK_REF.md` and `docs/overview/PROJECT_SUMMARY.md` for structure
- Agent docs under `docs/guides/` and `docs/reference/AGENT1_QUICK_REF.md`

## Backward Compatibility

- Defaults remain sensible; environments override YAML; YAML overrides code
- FAISS remains default unless `RAG_VECTORSTORE=chroma`

## Follow-ups (optional)

- Add `.gitignore` entries for `data/uploads/` and `data/chroma_db/`
- Mount `../config:/app/config` in compose if external YAML is required in-container
- Implement manual RAG backend using native Chroma client (Phase 2)

## Checklist

- [x] Code builds and containers start
- [x] Health endpoint returns 200
- [x] Test runner passes locally
- [x] Docs updated and organized
- [x] No remaining hardcoded data paths in code defaults
