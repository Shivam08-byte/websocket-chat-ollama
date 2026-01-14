# ChromaDB Integration Plan

## Objective
Add ChromaDB as a persistent vector store option for the project alongside the existing FAISS-based approach, enabling durable storage, faster incremental updates, and easier dataset management.

## Scope
- LangChain-based RAG path: add `Chroma` as an alternative to `FAISS` with drop-in configuration.
- Optional manual path: provide a lightweight integration using the native `chromadb` client.
- Keep current FAISS behavior as default and enable Chroma via config.

## Deliverables
- Config flag to choose vector store: `RAG_VECTORSTORE=faiss|chroma` (default: `faiss`).
- Persistent directory for Chroma data: `RAG_VECTORSTORE_PATH=/app/data/chroma_db`.
- Updated LangChain implementation to support `Chroma`.
- Optional: Minimal manual integration (`RAGStore` alternative) using native Chroma client.
- Documentation and basic tests.

## Dependencies
- Add to requirements.txt:
  - `chromadb>=0.5.0`
  - (already present) `langchain`, `langchain-community`
  - Note: We will reuse `OllamaEmbeddings` to avoid extra embedding deps.

## Architecture Changes
1. LangChain path (`app_langchain/langchain_rag.py`):
   - Introduce `vectorstore_type: Literal["faiss", "chroma"]` with env override `RAG_VECTORSTORE`.
   - If `faiss`: keep existing flow.
   - If `chroma`:
     - Import `Chroma` from `langchain_community.vectorstores`.
     - Use `Chroma.from_documents(documents, self.embeddings, persist_directory=self.vectorstore_path)`.
     - On updates (`add_documents`), call `self.vectorstore.add_documents(documents)` and then `self.vectorstore.persist()`.
     - For querying, use `self.vectorstore.as_retriever(search_kwargs={"k": top_k})`.
   - Make `vectorstore_path` configurable and point to `/app/data/chroma_db` by default when using Chroma.

2. Manual path (`app_manual/rag_store.py`):
   - Optional phase 2: Add `ChromaRAGStore` backed by the native `chromadb` client:
     - `client = chromadb.PersistentClient(path=vectorstore_path)`
     - `collection = client.get_or_create_collection("docs")`
     - `collection.add(documents=[...], metadatas=[...], ids=[...])`
     - `collection.query(query_texts=[query], n_results=top_k)`
   - Gate with `RAG_BACKEND=manual-json|manual-chroma` (default: `manual-json`).

## API/Config
- New envs:
  - `RAG_VECTORSTORE=faiss|chroma` (default `faiss`)
  - `RAG_VECTORSTORE_PATH=/app/data/chroma_db`
  - For manual optional path: `RAG_BACKEND=manual-json|manual-chroma`

## Data & Persistence
- Ensure `builds/docker-compose.yml` mounts the `/app/data` volume (already present). Chroma persistence will reuse it.
- Add a `data/.gitignore` rule to keep Chroma files out of git if needed (they live under `/app/data`).

## Migration Strategy
- Provide a one-time script/endpoint to rebuild the Chroma index from current uploads:
  - Iterate through saved uploads (if enabled) or in-memory doc registry and call `add_documents` with Chroma selected.
- No destructive change to FAISS; both can coexist while toggled via env.

## Testing Plan
- Unit-level
  - Ingestion: adding text and files produces embeddings and persists to Chroma directory.
  - Query: top-k retrieval returns expected metadata and content.
  - Filter by `sources`: only relevant docs used when provided.
  - Persistence: restart app and ensure Chroma loads existing collection.
- Integration-level
  - Endpoints `/api/rag/langchain/*` behave identically under FAISS and Chroma, aside from persistence.

## Rollout Plan
1. Phase 1 (LangChain only)
   - Add dependencies and env flags.
   - Implement Chroma path in `langchain_rag.py`.
   - Minimal docs and smoke tests.
2. Phase 2 (Optional manual store)
   - Implement `ChromaRAGStore` and switchable backend.
   - Add migration helper and extended docs.

## Code Changes (High Level)
- `app_langchain/langchain_rag.py`
  - Add `vectorstore_type` param, read `RAG_VECTORSTORE`.
  - On init: set `self.vectorstore_path` based on type.
  - `add_documents()`: branch for FAISS vs Chroma, call `persist()` for Chroma.
  - `query_with_rag()`: use `as_retriever` for either store.
- `app_langchain/app.py`
  - Read new envs and pass through to `LangChainRAGSystem`.
- `requirements.txt`
  - Add `chromadb`.
- `docs/SETUP.md`
  - Document enabling Chroma and data path.

## Operational Notes
- Chroma runs in-process via Python package; no external server needed.
- Ensure memory settings are reasonable for embedding size; consider `RAG_TOP_K` defaults.
- For large datasets, consider periodic `persist()` and compaction; monitor disk usage under `/app/data/chroma_db`.

## Backout
- Set `RAG_VECTORSTORE=faiss` to revert immediately without code changes.

---

### Quick Start (once implemented)
1) Enable Chroma via env:
```
RAG_VECTORSTORE=chroma
RAG_VECTORSTORE_PATH=/app/data/chroma_db
```
2) Rebuild and run containers:
```
docker compose up -d --build
```
3) Ingest and query via existing endpoints under `/api/rag/langchain/*`.
