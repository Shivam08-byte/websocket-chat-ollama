# Understanding RAG (Retrieval-Augmented Generation) - No Code Edition

## 🎯 What is RAG?

**RAG = Retrieval-Augmented Generation**

Think of it like this:
- **Without RAG**: You ask an AI a question, it only knows what was in its training data (like asking someone who only read books from 2 years ago)
- **With RAG**: You give the AI specific documents to reference, and it answers based on THOSE documents (like giving someone your company's handbook and asking questions about it)

**Analogy**: Imagine you're taking an open-book exam. RAG is like being able to quickly flip to the right pages in your textbook to answer each question.

---

## 📚 The Complete RAG Flow in Your Application

### Phase 1: Document Upload (Frontend)

**What happens:**
1. User clicks the "＋" button in the chat interface
2. Browser opens a file picker
3. User selects a document (PDF, DOCX, TXT, or Markdown)
4. JavaScript sends the file to the backend via `/api/rag/ingest_file`

**Why this matters:**
This is where your knowledge base starts. Each document you upload becomes searchable context for the AI.

---

### Phase 2: Text Extraction (Backend)

**What happens:**
The backend receives the file and extracts raw text based on file type:

**For PDFs:**
- Opens the PDF
- Goes through each page
- Extracts all readable text (doesn't work on scanned/image-only PDFs)
- Combines all pages into one long text string

**For DOCX (Word documents):**
- Opens the document
- Extracts text from all paragraphs
- Combines into one text string

**For TXT/Markdown:**
- Simply reads the file as plain text

**Analogy**: Like photocopying a book but only keeping the text, not the pictures or formatting.

**Important**: If a file has no extractable text (like a scanned image PDF), the system returns an error: "No text extracted from PDF."

---

### Phase 3: Text Chunking

**What happens:**
The long text is broken into smaller pieces called "chunks."

**Why chunk?**
- AI models have token limits (can't process infinite text at once)
- Smaller chunks are faster to search
- More precise retrieval (grab just the relevant paragraph, not the whole book)

**Your settings:**
- **Chunk size**: 800 characters per chunk
- **Overlap**: 200 characters overlap between consecutive chunks

**Why overlap?**
If an important sentence is split between two chunks, the overlap ensures context isn't lost.

**Analogy**: Like creating index cards for a textbook. Each card has a small section, and consecutive cards share a little bit of text so you don't lose context when reading them.

**Example:**
```
Original text: "Python is a programming language. It's used for web development, data science, and AI. Python has a simple syntax..."

Chunk 1 (800 chars):
"Python is a programming language. It's used for web development, data science, and AI. Python has a simple syntax..."

Chunk 2 (800 chars, with 200 char overlap):
"...Python has a simple syntax and is beginner-friendly. Many companies use Python for backend systems..."
```

---

### Phase 4: Embedding Generation (The Magic Part)

**What happens:**
Each chunk is converted into a **vector** (a list of numbers) called an **embedding**.

**What's an embedding?**
An embedding is a numerical representation of the *meaning* of text.

**Key concept**: Text chunks with similar meanings have similar embeddings (the numbers are close to each other).

**How it works:**
1. Each chunk is sent to the **Ollama embedding model** (`nomic-embed-text`)
2. The model analyzes the text and returns a vector (e.g., `[0.23, -0.45, 0.78, ...]` with hundreds of numbers)
3. This vector captures the semantic meaning of that chunk

**Analogy**: Like giving each chunk a "fingerprint" that represents its meaning. Similar topics have similar fingerprints.

**Example:**
- Chunk: "Python is great for data science" → Embedding: `[0.1, 0.8, -0.3, ...]`
- Chunk: "Machine learning uses Python often" → Embedding: `[0.12, 0.79, -0.28, ...]` (very similar!)
- Chunk: "I like pizza" → Embedding: `[-0.5, 0.2, 0.9, ...]` (completely different!)

**Why embeddings?**
They allow the system to find semantically similar text, even if the exact words are different.

Query: "What language is good for ML?"
Will match: "Python is great for data science" (even though "ML" and "machine learning" aren't in the chunk!)

---

### Phase 5: Storage

**What happens:**
Each chunk is saved to a JSON file (`rag_store.json`) with:
- **id**: Unique identifier for the chunk
- **text**: The actual text content
- **source**: The filename (e.g., `sdwp19.pdf`)
- **embedding**: The vector representation

**Structure:**
```
{
  "embed_model": "nomic-embed-text",
  "chunks": [
    {
      "id": "uuid-123",
      "text": "Python is a programming language...",
      "source": "sdwp19.pdf",
      "embedding": [0.23, -0.45, 0.78, ...]
    },
    {
      "id": "uuid-456",
      "text": "Machine learning is...",
      "source": "sdwp19.pdf",
      "embedding": [0.12, 0.79, -0.28, ...]
    }
  ]
}
```

**Why JSON?**
Simple, human-readable, and works for small-to-medium datasets. For production, you'd use a vector database like Pinecone, Weaviate, or Qdrant.

---

### Phase 6: User Query (When You Chat)

**What happens when you send a message:**

1. **Frontend**: You type "What is the title of the doc?" and click Send
2. **WebSocket payload** includes:
   - Your message: `"What is the title of the doc?"`
   - Active source: `["sdwp19.pdf"]` (if you attached a document)

**Important**: If you haven't attached a document (no chip showing), the `sources` field is `null`, and the system skips RAG entirely. This is **per-chat RAG scoping**.

---

### Phase 7: Query Embedding

**What happens:**
Your question is converted into a vector, just like the chunks were.

**Process:**
1. Query: "What is the title of the doc?"
2. Sent to Ollama embedding model
3. Returns query embedding: `[0.15, 0.82, -0.31, ...]`

**Why?**
So we can compare your question's "meaning" to the chunks' "meanings" using math.

---

### Phase 8: Retrieval (Finding Relevant Chunks)

**What happens:**
The system searches through all chunks to find the most relevant ones.

**How it works:**

1. **Filter by source**: Only look at chunks from `sdwp19.pdf` (the file you attached)
2. **Calculate similarity**: Compare your query embedding to each chunk's embedding using **cosine similarity**

**What's cosine similarity?**
A math formula that measures how "close" two vectors are. Returns a score from -1 to 1:
- **1.0** = Perfect match (identical meaning)
- **0.5** = Somewhat similar
- **0.0** = Completely unrelated
- **-1.0** = Opposite meanings

**Analogy**: Like measuring the angle between two arrows. If they point in the same direction, they're similar.

3. **Rank by score**: Sort chunks by similarity score (highest first)
4. **Return top-k chunks**: Grab the top 4 most relevant chunks (your `RAG_TOP_K=4` setting)

**Example:**
```
Query: "What is the title of the doc?"
Query embedding: [0.15, 0.82, -0.31, ...]

Chunk 1: "The title is 'Advanced FastAPI Patterns'..." 
  → Similarity: 0.89 ✅ (high match!)

Chunk 2: "Chapter 1: Introduction to microservices..."
  → Similarity: 0.45 (medium match)

Chunk 3: "Docker commands for deployment..."
  → Similarity: 0.12 (low match)

Result: Chunk 1 is returned because it has the highest score.
```

---

### Phase 9: Context Building

**What happens:**
The top chunks are formatted into a context block that will be given to the AI.

**Process:**
1. Take the top 4 chunks
2. Format each as:
   ```
   Source: sdwp19.pdf
   [chunk text here]
   ```
3. Combine them with separators: `\n\n---\n\n`
4. Limit to `RAG_MAX_CHARS=2000` characters to avoid overwhelming the LLM

**Example context block:**
```
Source: sdwp19.pdf
The title is 'Advanced FastAPI Patterns' and covers modern backend development practices.

---

Source: sdwp19.pdf
Chapter 1 introduces microservices architecture and explains how FastAPI enables rapid API development.
```

---

### Phase 10: Prompt Construction

**What happens:**
The retrieved context is injected into the prompt sent to the LLM.

**Without RAG (no document attached):**
```
You are a helpful AI assistant. Provide clear, concise, and accurate responses.

User: What is the title of the doc?
Assistant:
```

**With RAG (document attached):**
```
You are a helpful AI assistant. Provide clear, concise, and accurate responses.

You are given retrieved context from a knowledge base. Use it to answer the question.
If the answer isn't in the context, say you don't know.

Context:
Source: sdwp19.pdf
The title is 'Advanced FastAPI Patterns' and covers modern backend development practices.

---

Source: sdwp19.pdf
Chapter 1 introduces microservices architecture...

User: What is the title of the doc?
Assistant:
```

**Key instructions to the AI:**
- Use the context to answer
- If the answer isn't there, admit you don't know (prevents hallucination)

---

### Phase 11: LLM Generation

**What happens:**
The complete prompt (with context) is sent to the Ollama LLM (Gemma 2B by default).

**The AI:**
1. Reads the context
2. Sees your question
3. Generates an answer based on the retrieved chunks

**Example response:**
"The title of the document is 'Advanced FastAPI Patterns'."

---

### Phase 12: Response Display

**What happens:**
1. Backend sends the AI's response back through the WebSocket
2. Frontend displays it in the chat as an "AI" message
3. You see the answer!

---

## 🔄 Complete Flow Summary

```
1. USER uploads sdwp19.pdf via "＋" button
   ↓
2. BACKEND extracts text from PDF
   ↓
3. TEXT is split into chunks (800 chars each, 200 overlap)
   ↓
4. EMBEDDINGS are generated for each chunk via Ollama
   ↓
5. CHUNKS stored in rag_store.json with embeddings + source
   ↓
6. USER types "What is the title?" and sends message
   ↓
7. FRONTEND sends { message: "...", sources: ["sdwp19.pdf"] }
   ↓
8. BACKEND converts query to embedding
   ↓
9. RETRIEVAL: Compare query embedding to chunk embeddings (cosine similarity)
   ↓
10. TOP 4 most similar chunks are selected (only from sdwp19.pdf)
   ↓
11. CONTEXT BLOCK is built from those chunks
   ↓
12. PROMPT is constructed: system prompt + context + user question
   ↓
13. LLM (Gemma 2B) generates answer using the context
   ↓
14. RESPONSE sent back to user via WebSocket
   ↓
15. USER sees answer in chat!
```

---

## 🎨 Key Concepts

### 1. **Semantic Search**
Traditional search: Looks for exact word matches ("title" in document)
RAG search: Looks for meaning matches (understands "title" = "name of doc" = "heading")

### 2. **Per-Chat Scoping**
Each chat session can attach its own document. The system only searches chunks from that specific document. This prevents cross-contamination between different conversations.

### 3. **Vector Similarity**
The entire system relies on measuring "closeness" between vectors (embeddings). Similar meanings → similar vectors → high cosine similarity score.

### 4. **Context Window Management**
LLMs have token limits. By retrieving only the top 4 chunks and limiting to 2000 chars, we give the AI enough context without exceeding limits.

---

## 🛠️ Your Configuration

| Setting | Value | What it does |
|---------|-------|--------------|
| `RAG_ENABLED` | `true` | RAG system is active |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model used for generating embeddings |
| `RAG_TOP_K` | `4` | Return top 4 most relevant chunks |
| `RAG_MAX_CHARS` | `2000` | Max characters in context block |
| `chunk_size` | `800` | Characters per chunk |
| `chunk_overlap` | `200` | Overlap between consecutive chunks |

---

## 💡 Why RAG is Powerful

1. **Up-to-date information**: Upload any document, even from today
2. **Private data**: Your company docs, personal notes, etc. (never part of training data)
3. **Reduced hallucination**: AI cites specific context, not making things up
4. **Transparency**: You know exactly what sources the AI is using
5. **Scalable**: Add 100 documents, still retrieves relevant chunks in milliseconds

---

## 🚨 Limitations

1. **Scanned PDFs**: Can't extract text from images (need OCR)
2. **JSON storage**: Slow for 10,000+ documents (use a vector DB in production)
3. **Chunk size matters**: Too small = lose context, too large = irrelevant info sneaks in
4. **Embedding quality**: Depends on the model (nomic-embed-text is good, but specialized embeddings can be better)
5. **No cross-document synthesis**: If the answer requires info from 2 separate docs, RAG might miss it

---

## 🎓 Analogies Recap

| RAG Component | Analogy |
|---------------|---------|
| Chunking | Creating index cards from a textbook |
| Embeddings | Giving each card a "fingerprint" of its meaning |
| Vector store | A filing cabinet organized by fingerprints |
| Query embedding | Getting a fingerprint for your question |
| Retrieval | Finding cards with similar fingerprints |
| Context building | Photocopying the relevant cards for the AI |
| LLM | A student answering your question using those photocopies |

---

## 🔮 Next Steps to Improve

1. **Add OCR**: Use Tesseract to handle scanned PDFs
2. **Switch to vector DB**: Pinecone, Weaviate, or Qdrant for better performance
3. **Hybrid search**: Combine semantic search with keyword search (BM25)
4. **Reranking**: Use a cross-encoder to re-sort retrieved chunks for better accuracy
5. **Metadata filtering**: Filter by date, author, document type, etc.
6. **Multi-document queries**: Allow querying across multiple attached documents
7. **Citation**: Show exact chunk sources in the AI response

---

## 📖 Further Reading

- **Embeddings**: How neural networks convert text to vectors
- **Vector databases**: Specialized DBs for fast similarity search
- **Cosine similarity vs. dot product**: Different ways to measure vector closeness
- **Sentence transformers**: Models specifically trained for embeddings
- **Hybrid search**: Combining dense (embeddings) and sparse (keywords) retrieval

---

**Congratulations! You now understand how your RAG system works from upload to answer.** 🎉
