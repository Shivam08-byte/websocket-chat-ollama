# Dual System Comparison: Manual vs LangChain

This application now supports **side-by-side comparison** of two RAG implementations:
1. **Manual Implementation** - Your custom-built RAG system
2. **LangChain Implementation** - Framework-based RAG using LangChain

## 🎯 How It Works

### Toggle Button (Top Right)
- **Manual** (default) - Uses your hand-crafted RAG system
- **LangChain** - Uses LangChain's built-in RAG components

Both systems:
- ✅ Run completely offline with Ollama
- ✅ Use the same models (Gemma 2B, nomic-embed-text)
- ✅ Support document upload and RAG
- ✅ Work with or without documents attached

## 📊 What Gets Compared

### Manual System (Your Implementation)
**File**: `rag_store.py`

**How it works**:
1. Manual text splitting (800 chars, 200 overlap)
2. Direct HTTP calls to Ollama for embeddings
3. JSON file storage (`/app/data/rag_store.json`)
4. NumPy cosine similarity calculations
5. Manual context building

**Pros**:
- Full control and understanding
- Minimal dependencies
- Optimized for your use case
- ~150 lines of code

### LangChain System
**File**: `app_langchain/langchain_rag.py`

**How it works**:
1. LangChain's `RecursiveCharacterTextSplitter`
2. LangChain's `OllamaEmbeddings` wrapper
3. FAISS vector database (in-memory)
4. LangChain's `RetrievalQA` chain
5. Automatic prompt templating

**Pros**:
- Industry-standard framework
- Pre-built components
- Easy to extend with agents
- Built-in prompt management

## 🚀 Usage

### 1. Upload a Document
Click the **"+"** button and select a file (PDF, DOCX, TXT, MD).

**Behind the scenes**:
- Document is indexed in **BOTH** systems simultaneously
- Manual system → JSON storage
- LangChain system → FAISS vectorstore

### 2. Toggle the System
Use the switch in the top right to change between:
- **Manual** (blue) - Your implementation
- **LangChain** (green) - Framework

### 3. Ask Questions
With a document attached:
- **RAG-enabled**: Both systems retrieve relevant chunks
- Without document: Both do direct LLM queries

### 4. Compare Results
Try the same question with both systems and compare:
- Response quality
- Response time
- Context retrieval accuracy

## 🔍 What to Compare

### Test Case 1: Simple Factual Question
**Document**: Technical document (e.g., your PDF)
**Question**: "What is the title of this document?"

**Expected**: Both should extract the title accurately.

### Test Case 2: Semantic Understanding
**Question**: "Explain the main concepts"

**Expected**: Both retrieve relevant chunks, but may differ in:
- Which chunks are selected
- Order of relevance
- Context window size

### Test Case 3: No Document (Direct LLM)
**Question**: "What is Python?" (no document attached)

**Expected**: Both call LLM directly, similar responses.

### Test Case 4: Multi-hop Reasoning
**Question**: "Compare X and Y mentioned in the document"

**Expected**: See how each system handles connecting information from multiple chunks.

## 📈 Statistics Endpoint

Check stats for both systems:
```bash
curl http://localhost:8081/api/rag/stats
```

Response:
```json
{
  "manual": {
    "enabled": true,
    "chunks": 17,
    "sources": {"sdwp19.pdf": 17},
    "embed_model": "nomic-embed-text"
  },
  "langchain": {
    "total_chunks": 18,
    "sources": {"sdwp19.pdf": 18},
    "embed_model": "nomic-embed-text",
    "llm_model": "gemma:2b",
    "system": "langchain"
  },
  "current_system": "manual"
}
```

**Note**: Chunk counts may differ slightly due to different splitting algorithms.

## 🧪 Debugging

### Check Logs
```bash
docker compose logs -f fastapi
```

Look for:
- `[LangChain]` - LangChain system messages
- `WS message received | system=Manual|LangChain` - Which system handled the query

### Browser Console
Open DevTools (F12) and check console for:
```
[DEBUG] useLangchain: true/false
[SYSTEM] Switched to: Manual/LangChain
```

## 🎓 Learning Observations

### Code Complexity
- **Manual**: ~150 lines (rag_store.py)
- **LangChain**: ~250 lines (langchain_rag.py) but handles more features

### Key Differences

| Feature | Manual | LangChain |
|---------|--------|-----------|
| **Text Splitting** | Fixed 800 chars | Recursive by separators |
| **Vector Storage** | JSON file | FAISS in-memory |
| **Search** | Manual cosine sim | FAISS optimized |
| **Prompt Templates** | String concat | PromptTemplate class |
| **Context Building** | Manual loop | RetrievalQA chain |
| **Extensibility** | Add code | Use LangChain features |

### Performance
- **Manual**: Slightly faster for small datasets (no framework overhead)
- **LangChain**: Faster for large datasets (FAISS optimization)

### When to Use Each

**Use Manual when**:
- Learning fundamentals
- Need full control
- Simple use case
- Minimal dependencies

**Use LangChain when**:
- Building agents (next stage!)
- Need prompt management
- Multiple data sources
- Production scale

## 🚀 Next Steps

### For Manual System
- Add metadata filtering
- Implement hybrid search (BM25 + semantic)
- Add reranking

### For LangChain System
- Add agents with tools (calculator, weather)
- Implement conversation memory
- Use LangGraph for multi-step workflows

## 💡 Pro Tips

1. **Upload the same document** to both systems for fair comparison
2. **Clear browser cache** when switching to see fresh results
3. **Check logs** to see which chunks were retrieved by each system
4. **Test edge cases**: empty queries, very long documents, multiple sources

## 🎯 Expected Learnings

After testing both systems, you'll understand:
- ✅ How LangChain simplifies complex operations
- ✅ Trade-offs between control and convenience
- ✅ Where frameworks add value vs overhead
- ✅ When to build from scratch vs use frameworks

## 🔧 Troubleshooting

### LangChain system not working?
Check if FAISS is installed:
```bash
docker compose exec fastapi python -c "import faiss; print('FAISS OK')"
```

### Both systems giving different results?
Normal! Different chunking strategies lead to different retrievals. Compare:
1. Chunk boundaries
2. Overlap handling
3. Similarity thresholds

### Toggle not updating?
Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

---

**Enjoy comparing both systems! This is the best way to understand what LangChain does under the hood.** 🚀
