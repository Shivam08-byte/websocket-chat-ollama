# Complete Chat Serving Flow - WebSocket Chat with Ollama

## Overview

This document provides a detailed flow of how a chat message travels through the entire system, from user input to AI response display.

---

## 🔄 High-Level Flow Diagram

```
┌─────────┐      ┌──────────┐      ┌─────────┐      ┌─────────┐
│ Browser │ ───▶ │ FastAPI  │ ───▶ │ Ollama  │ ───▶ │   AI    │
│   UI    │      │WebSocket │      │   API   │      │  Model  │
│         │ ◀─── │  Server  │ ◀─── │         │ ◀─── │         │
└─────────┘      └──────────┘      └─────────┘      └─────────┘
```

---

## 📊 Detailed Flow Breakdown

### Phase 1: Application Initialization

#### 1.1 Docker Container Startup
```
docker-compose up -d
    │
    ├─▶ Start Ollama Container
    │   ├─ Pull specified model (OLLAMA_MODEL)
    │   └─ Start Ollama API server (port 11434)
    │
    └─▶ Start FastAPI Container
        ├─ Load environment variables (.env)
        ├─ Initialize FastAPI app
        ├─ Mount static files (/static)
        └─ Start Uvicorn server (port 8000)
```

#### 1.2 Frontend Loading
```
User opens http://localhost:8081
    │
    ├─▶ Browser requests index.html
    │   ├─ FastAPI serves static/index.html
    │   ├─ Browser loads static/style.css
    │   └─ Browser loads static/script.js
    │
    └─▶ JavaScript Initialization (script.js)
        ├─ Call loadAvailableModels()
        │  └─ GET /api/models → Populate dropdown
        │
        └─ Call connect()
           └─ Establish WebSocket connection
```

---

### Phase 2: WebSocket Connection Establishment

#### 2.1 Client-Side Connection (script.js)
```javascript
Location: static/script.js, function connect()

1. Determine protocol: ws:// or wss://
2. Construct WebSocket URL: ws://localhost:8081/ws
3. Create WebSocket instance: new WebSocket(wsUrl)
4. Attach event handlers:
   - ws.onopen    → Update status to "Connected"
   - ws.onmessage → handleMessage(data)
   - ws.onerror   → Log error, update status
   - ws.onclose   → Attempt reconnection after 3s
```

#### 2.2 Server-Side Connection (app.py)
```python
Location: app.py, @app.websocket("/ws")

1. Accept WebSocket connection
   await manager.connect(websocket)
   
2. Add to active connections list
   manager.active_connections.append(websocket)
   
3. Send welcome message
   {
     "type": "system",
     "message": "Connected to chat server..."
   }
   
4. Enter message listening loop
   while True:
       data = await websocket.receive_text()
```

---

### Phase 3: User Sends Message

#### 3.1 User Input (Browser)
```
User types message "What is Python?"
User presses Enter or clicks "Send" button
    │
    └─▶ Event: messageInput.keypress or sendButton.click
```

#### 3.2 Frontend Processing (script.js)
```javascript
Location: static/script.js, function sendMessage()

1. Get message text
   const message = messageInput.value.trim();
   
2. Validate
   - Check if message is not empty
   - Check if WebSocket is open (ws.readyState === WebSocket.OPEN)
   
3. Send via WebSocket
   ws.send(JSON.stringify({ message }));
   
4. Clear input field
   messageInput.value = '';
```

**Message Payload:**
```json
{
  "message": "What is Python?"
}
```

---

### Phase 4: Server Receives and Processes Message

#### 4.1 WebSocket Endpoint (app.py)
```python
Location: app.py, websocket_endpoint()

1. Receive message
   data = await websocket.receive_text()
   
2. Parse JSON
   message_data = json.loads(data)
   user_message = message_data.get("message", "")
   
3. Validate
   if not user_message.strip():
       continue  # Skip empty messages
```

#### 4.2 Echo User Message
```python
Location: app.py, websocket_endpoint()

Send user message back to client for display:

await manager.send_message(
    json.dumps({
        "type": "user",
        "message": user_message
    }),
    websocket
)
```

**Message sent to client:**
```json
{
  "type": "user",
  "message": "What is Python?"
}
```

#### 4.3 Send Typing Indicator
```python
Location: app.py, websocket_endpoint()

await manager.send_message(
    json.dumps({
        "type": "typing",
        "message": "AI is typing..."
    }),
    websocket
)
```

---

### Phase 5: Query Ollama AI

#### 5.1 Prepare Prompt (app.py)
```python
Location: app.py, async def query_ollama(prompt: str)

1. Create system prompt
   system_prompt = "You are a helpful AI assistant..."
   
2. Format full prompt
   full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
   
   Result:
   "You are a helpful AI assistant. Provide clear, concise responses.
    
    User: What is Python?
    Assistant:"
```

#### 5.2 HTTP Request to Ollama
```python
Location: app.py, query_ollama()

async with httpx.AsyncClient(timeout=120) as client:
    response = await client.post(
        f"{OLLAMA_HOST}/api/generate",  # http://ollama:11434/api/generate
        json={
            "model": current_model,      # e.g., "gemma:2b"
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 200,
                "stop": ["\nUser:", "User:", "\n\n\n"]
            }
        }
    )
```

**Request to Ollama:**
```json
{
  "model": "gemma:2b",
  "prompt": "You are a helpful AI assistant...\n\nUser: What is Python?\nAssistant:",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 200,
    "stop": ["\nUser:", "User:", "\n\n\n"]
  }
}
```

---

### Phase 6: Ollama Processes Request

#### 6.1 Ollama API (Inside Ollama Container)
```
1. Receive HTTP POST at /api/generate

2. Load model into memory (if not already loaded)
   - Model: gemma:2b
   - Size: ~1.7 GB
   
3. Process prompt through model
   - Apply temperature: 0.7
   - Apply top_p: 0.9
   - Apply top_k: 40
   - Generate up to 200 tokens
   - Stop at defined sequences
   
4. Generate response text
   "Python is a high-level, interpreted programming language known for its
    simplicity and readability. It's widely used in web development, data
    science, automation, and more."
   
5. Return JSON response
```

**Response from Ollama:**
```json
{
  "model": "gemma:2b",
  "created_at": "2024-01-05T10:30:00Z",
  "response": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, automation, and more.",
  "done": true,
  "total_duration": 3500000000,
  "load_duration": 500000000,
  "prompt_eval_count": 45,
  "eval_count": 52
}
```

---

### Phase 7: Server Processes AI Response

#### 7.1 Extract Response (app.py)
```python
Location: app.py, query_ollama()

if response.status_code == 200:
    result = response.json()
    response_text = result.get("response", "No response from model")
    response_text = response_text.strip()
    return response_text
```

#### 7.2 Send AI Response to Client
```python
Location: app.py, websocket_endpoint()

await manager.send_message(
    json.dumps({
        "type": "ai",
        "message": ai_response
    }),
    websocket
)
```

**Message sent to client:**
```json
{
  "type": "ai",
  "message": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, automation, and more."
}
```

---

### Phase 8: Client Displays Response

#### 8.1 WebSocket Message Handler (script.js)
```javascript
Location: static/script.js, ws.onmessage

1. Receive message
   ws.onmessage = (event) => {
       const data = JSON.parse(event.data);
       handleMessage(data);
   }
   
2. Parse message type
   const { type, message } = data;
```

#### 8.2 Handle Message by Type
```javascript
Location: static/script.js, handleMessage()

switch(type) {
    case 'user':
        // Display user message (already shown)
        break;
        
    case 'typing':
        // Show typing indicator
        showTypingIndicator(message);
        break;
        
    case 'ai':
        // Remove typing indicator
        removeTypingIndicator();
        // Display AI response
        addMessage(message, 'ai');
        break;
        
    case 'system':
        addMessage(message, 'system');
        break;
        
    case 'error':
        addMessage(message, 'error');
        break;
}
```

#### 8.3 Display Message (script.js)
```javascript
Location: static/script.js, addMessage()

1. Create message element
   const messageDiv = document.createElement('div');
   messageDiv.className = `message ai`;
   messageDiv.textContent = "Python is a high-level...";
   
2. Append to messages container
   messagesContainer.appendChild(messageDiv);
   
3. Auto-scroll to bottom
   scrollToBottom();
```

---

## 🎯 Complete Message Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                                           │
│    User types: "What is Python?"                                        │
│    User presses Enter                                                   │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. FRONTEND PROCESSING (script.js)                                      │
│    - Validate input                                                     │
│    - Send via WebSocket: {"message": "What is Python?"}                 │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ WebSocket (ws://)
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. WEBSOCKET ENDPOINT (app.py)                                          │
│    - Receive message                                                    │
│    - Parse JSON                                                         │
│    - Echo user message back                                             │
│    - Send typing indicator                                              │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. QUERY OLLAMA (app.py - query_ollama())                               │
│    - Format system prompt                                               │
│    - Create full prompt with context                                    │
│    - Configure generation options                                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ HTTP POST
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. OLLAMA API (http://ollama:11434/api/generate)                        │
│    - Receive HTTP request                                               │
│    - Load model: gemma:2b                                               │
│    - Process prompt                                                     │
│    - Generate response                                                  │
│    - Return JSON                                                        │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ HTTP Response
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. PROCESS AI RESPONSE (app.py)                                         │
│    - Extract response text                                              │
│    - Clean and format                                                   │
│    - Send via WebSocket: {"type": "ai", "message": "..."}               │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. FRONTEND DISPLAY (script.js)                                         │
│    - Receive WebSocket message                                          │
│    - Parse JSON                                                         │
│    - Remove typing indicator                                            │
│    - Create message element                                             │
│    - Append to chat                                                     │
│    - Auto-scroll                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Key Components and Their Roles

### 1. **Frontend (static/script.js)**
- **Role**: User interface and WebSocket client
- **Responsibilities**:
  - Capture user input
  - Send messages via WebSocket
  - Receive and display messages
  - Handle connection status
  - Manage model selection

### 2. **FastAPI Server (app.py)**
- **Role**: WebSocket server and API gateway
- **Responsibilities**:
  - Accept WebSocket connections
  - Manage active connections
  - Route messages between client and Ollama
  - Format prompts
  - Handle errors

### 3. **Ollama Service**
- **Role**: AI model hosting and inference
- **Responsibilities**:
  - Host LLM models
  - Process generation requests
  - Return AI-generated text
  - Manage model loading/unloading

### 4. **Docker Compose**
- **Role**: Container orchestration
- **Responsibilities**:
  - Start/stop services
  - Network configuration
  - Volume management
  - Environment variables

---

## ⏱️ Timing Breakdown

| Phase | Component | Average Time |
|-------|-----------|-------------|
| 1. User Input | Browser | ~0ms (instant) |
| 2. WebSocket Send | Network | ~1-5ms (local) |
| 3. Server Processing | FastAPI | ~10-20ms |
| 4. Prompt Formatting | FastAPI | ~1-2ms |
| 5. HTTP Request | FastAPI → Ollama | ~5-10ms |
| 6. AI Inference | Ollama + Model | **2-10 seconds** |
| 7. Response Processing | FastAPI | ~5-10ms |
| 8. WebSocket Send | Network | ~1-5ms |
| 9. Display Update | Browser | ~10-20ms |
| **Total** | | **~2-10 seconds** |

*Note: Most time is spent in AI inference (Phase 6)*

---

## 🔄 Error Handling Flow

### Frontend Errors
```
Error Detected
    │
    ├─▶ Connection Lost
    │   ├─ Update status to "Disconnected"
    │   ├─ Disable send button
    │   └─ Attempt reconnection after 3s
    │
    ├─▶ Empty Message
    │   └─ Ignore (do nothing)
    │
    └─▶ Model Loading Failed
        ├─ Display error message
        ├─ Re-enable controls
        └─ Keep previous model selected
```

### Backend Errors
```
Error Detected
    │
    ├─▶ WebSocket Disconnected
    │   ├─ Remove from active connections
    │   └─ Exit message loop
    │
    ├─▶ Ollama Connection Failed
    │   ├─ Return error message
    │   └─ Send via WebSocket: {"type": "error", "message": "..."}
    │
    ├─▶ Invalid JSON
    │   ├─ Send error message
    │   └─ Continue listening
    │
    └─▶ Timeout
        ├─ Catch httpx.TimeoutException
        └─ Return timeout message
```

---

## 🎨 Message Types and Styling

| Type | CSS Class | Purpose | Display Style |
|------|-----------|---------|---------------|
| `user` | `.message.user` | User's message | Right-aligned, purple gradient |
| `ai` | `.message.ai` | AI response | Left-aligned, white with border |
| `system` | `.message.system` | System notifications | Centered, yellow background |
| `error` | `.message.error` | Error messages | Centered, red background |
| `typing` | `.message.typing` | Typing indicator | Left-aligned, gray, italic |
| `loading` | `.message.loading` | Model loading | Centered, blue background |

---

## 🔌 WebSocket Protocol Details

### Message Format
All messages are JSON strings with this structure:
```json
{
  "type": "user" | "ai" | "system" | "error" | "typing" | "loading",
  "message": "actual message content"
}
```

### Connection Lifecycle
```
1. Client connects → ws://localhost:8081/ws
2. Server accepts → await websocket.accept()
3. Server adds to connection pool
4. Server sends welcome message
5. Server enters message loop
6. Messages exchanged bidirectionally
7. Client disconnects or connection lost
8. Server removes from connection pool
9. Client attempts reconnection (if available)
```

---

## 📝 Configuration Flow

### Startup Configuration
```
docker-compose.yml
    │
    ├─▶ Load .env file
    │   ├─ OLLAMA_MODEL=gemma:2b
    │   ├─ FASTAPI_PORT=8000
    │   ├─ OLLAMA_HOST=http://ollama:11434
    │   └─ etc.
    │
    ├─▶ Pass to containers as environment variables
    │
    └─▶ app.py reads environment variables
        └─ Configure FastAPI and Ollama connection
```

### Runtime Configuration
```
User selects model from dropdown
    │
    ├─▶ POST /api/models/load
    │
    ├─▶ Update global current_model variable
    │
    ├─▶ Ollama pulls model if needed
    │
    └─▶ Return success/failure
```

---

## 🚀 Performance Optimization Points

1. **WebSocket Reuse**: Single persistent connection vs. HTTP polling
2. **Async Processing**: Non-blocking I/O for concurrent users
3. **Model Caching**: Models stay in memory after first use
4. **Response Limiting**: Max 200 tokens prevents overly long responses
5. **Stop Sequences**: Prevents model from generating unnecessary text
6. **Client-Side Validation**: Reduces unnecessary network requests

---

## 📚 Related Files Reference

- **Frontend**: [`static/index.html`](static/index.html), [`static/script.js`](static/script.js), [`static/style.css`](static/style.css)
- **Backend**: [`app.py`](app.py)
- **Configuration**: [`.env`](.env), [`docker-compose.yml`](docker-compose.yml)
- **Documentation**: [`README.md`](README.md), [`SETUP.md`](SETUP.md), [`MODEL_SELECTION.md`](MODEL_SELECTION.md)

---

## ✅ Flow Verification Checklist

To verify the complete flow is working:

- [ ] WebSocket connection established (green indicator)
- [ ] Model dropdown populated
- [ ] Send button enabled
- [ ] User message displays on right
- [ ] Typing indicator appears
- [ ] AI response displays on left
- [ ] Auto-scroll works
- [ ] Model switching works
- [ ] Error handling displays messages
- [ ] Reconnection works after disconnect

Run [`verify.sh`](verify.sh) to check system health.

---

## 🎓 Understanding the Flow

This chat application uses **WebSockets** for real-time, bidirectional communication, which is more efficient than traditional HTTP for chat applications:

- **HTTP**: Client requests → Server responds (one-way, request needed for updates)
- **WebSocket**: Persistent connection, both sides can send messages anytime

The AI processing happens **server-side** to:
- Keep API keys secure
- Manage model resources centrally
- Enable future features like chat history
- Allow multiple users to share models

---

**End of Flow Documentation** ✅