# Tests Directory

Automated and manual test scripts for the RAG streaming chat system.

## Available Tests

### `test_chroma.py`

Comprehensive test suite for ChromaDB vector store integration.

**Features:**
- Health check and API connectivity
- FAISS baseline validation
- ChromaDB ingestion tests
- Query tests (with/without source filtering)
- Persistence verification (requires manual restart)
- Source-based filtering tests

**Prerequisites:**
```bash
# Ensure requests library is available
pip install requests

# Start the application stack
cd builds
docker compose up -d
```

**Basic Usage:**
```bash
# Run all tests (default port 8000)
python tests/test_chroma.py

# Specify custom port
python tests/test_chroma.py --base-url http://localhost:8081

# Skip persistence test (no manual restart required)
python tests/test_chroma.py --skip-persistence

# Show help
python tests/test_chroma.py --help
```

**Test Scenarios:**

1. **FAISS Baseline Test**
   - Verifies ingestion with default FAISS vectorstore
   - Tests basic query functionality
   - Validates source filtering

2. **ChromaDB Ingestion Test**
   - Ingests multiple documents
   - Verifies chunk counts
   - Validates stats endpoint

3. **ChromaDB Querying Test**
   - Tests queries with and without source filters
   - Validates response quality
   - Tests multiple query patterns

4. **ChromaDB Persistence Test** (manual step required)
   - Records pre-restart state
   - Prompts for container restart
   - Verifies data persisted after restart
   - **Note:** Only works when `RAG_VECTORSTORE=chroma`

5. **Source Filtering Test**
   - Tests single-source queries
   - Tests multi-source queries
   - Tests non-existent source handling

**Expected Output:**
```
============================================================
ChromaDB Vector Store Test Suite
============================================================

ℹ Target: http://localhost:8000
ℹ Timeout: 30s

============================================================
Pre-flight Check
============================================================

✓ Health check passed: {...}

[Test results with colored output]

============================================================
Test Summary
============================================================

✓ FAISS Baseline
✓ ChromaDB Ingestion
✓ ChromaDB Querying
✓ ChromaDB Persistence
✓ Source Filtering

Result: 5/5 tests passed

✓ All tests passed!
```

**Switching to ChromaDB for Tests:**

1. Configure environment:
   ```bash
   cd /Users/shivam/Desktop/workspace/poc/websockets
   
   # Add to .env or set in shell
   echo 'RAG_VECTORSTORE=chroma' >> .env
   echo 'RAG_VECTORSTORE_PATH=/app/data/chroma_db' >> .env
   ```

2. Rebuild and restart:
   ```bash
   cd builds
   docker compose down
   docker compose up -d --build
   docker compose logs -f fastapi
   ```

3. Run tests:
   ```bash
   python tests/test_chroma.py
   ```

**Troubleshooting:**

- **Connection refused**: Ensure containers are running with `docker compose ps`
- **Timeout errors**: Increase timeout with `--timeout 60`
- **Port mismatch**: Check `FASTAPI_EXTERNAL_PORT` in `.env` and use `--base-url`
- **Empty responses**: Verify Ollama pulled embedding model with `docker logs ollama`

**Exit Codes:**
- `0`: All tests passed
- `1`: One or more tests failed

## Future Tests

- `test_manual_rag.py` - Manual RAG system tests
- `test_websocket.py` - WebSocket streaming tests
- `test_agents.py` - Agent system tests
- `test_performance.py` - Performance benchmarks
