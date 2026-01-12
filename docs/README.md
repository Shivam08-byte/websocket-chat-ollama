# WebSocket Chat with Ollama LLM

A Proof of Concept (POC) demonstrating real-time chat with an AI using WebSockets, FastAPI, and Ollama.

> **📖 New to this project? Start with [SETUP.md](SETUP.md) for detailed setup instructions for any device!**

## Features

- 🚀 **Real-time Communication**: WebSocket-based chat for instant messaging
- 🤖 **AI Integration**: Powered by Ollama with multiple LLM models
- 🔄 **Model Selection**: Switch between different AI models on-the-fly
- 🐳 **Dockerized**: Complete containerized setup with Docker Compose
- 🎨 **Modern UI**: Clean and responsive chat interface
- ⚡ **FastAPI Backend**: High-performance Python web framework

## Project Structure

```
websockets/
├── app.py                 # FastAPI application with WebSocket endpoint
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container for FastAPI app
├── docker-compose.yml    # Orchestrates Ollama and FastAPI services
├── .env                  # Environment configuration (create from .env.example)
├── .env.example          # Example environment configuration
├── static/
│   ├── index.html       # Chat interface
│   ├── style.css        # Styling
│   └── script.js        # WebSocket client logic
└── README.md
```

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 4GB of free RAM (for Ollama and Llama2 model)
- Internet connection for initial setup

## Quick Start

### 1. Clone or navigate to the project directory

```bash
cd /Users/shivam/Desktop/workspace/poc/websockets
```

### 2. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to customize your configuration:

```bash
# Application Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama2              # Change to mistral, codellama, etc.
OLLAMA_TIMEOUT=120

# Docker Ports
FASTAPI_EXTERNAL_PORT=8000
OLLAMA_EXTERNAL_PORT=11434
```

### 3. Start the services

```bash
docker-compose up --build
```

This will:
- Pull the Ollama Docker image
- Download the model specified in `.env` (default: Llama2, ~4GB)
- Build the FastAPI application
- Start both services

**Note**: First startup will take several minutes to download the model.

### 4. Access the chat interface

Open your browser and go to:
```
http://localhost:8000
```

## Available AI Models

The application comes pre-configured with multiple AI models:

| Model | Size | Best For |
|-------|------|----------|
| **Gemma 2B** (default) | 1.7 GB | General conversations, good balance |
| **Phi-3 Mini** | 2.3 GB | Reasoning, technical questions |
| **Llama 3.2 1B** | 1.3 GB | Fast responses, lightweight |
| **Qwen 2.5 1.5B** | 934 MB | Multilingual support |

### Switching Models

1. Use the dropdown in the top-right corner of the chat interface
2. Select your desired model
3. Wait for it to load (first time only, ~30s-2min depending on model)
4. Start chatting once you see "loaded successfully"

### Pre-loading All Models (Optional)

To download all models at once:

```bash
./pull-all-models.sh
```

This downloads all 4 models (~6-8 GB total). Models are cached and load instantly after first download.

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User's Browser                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Chat UI (http://localhost:8081)                │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │  │
│  │  │   Header    │  │    Model     │  │  Connection Status     │  │  │
│  │  │   & Title   │  │   Selector   │  │      Indicator         │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────────────────┐  │  │
│  │  │                                                             │  │  │
│  │  │              Chat Messages Area                            │  │  │
│  │  │   [User Message]                                           │  │  │
│  │  │              [AI Response]                                 │  │  │
│  │  │   [User Message]                                           │  │  │
│  │  │              [AI Response]                                 │  │  │
│  │  │                                                             │  │  │
│  │  └───────────────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────┐  ┌──────────────┐            │  │
│  │  │  Message Input Field         │  │ Send Button  │            │  │
│  │  └──────────────────────────────┘  └──────────────┘            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                  ▲                                       │
│                                  │ HTML/CSS/JS                           │
│                                  │ (static/)                             │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
                        WebSocket Connection (WSS/WS)
                                   │
┌──────────────────────────────────▼───────────────────────────────────────┐
│                     Docker Container: fastapi_websocket                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                   FastAPI Application (app.py)                    │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │  │
│  │  │   WebSocket     │  │   REST API       │  │   Static File  │  │  │
│  │  │   Endpoint      │  │   Endpoints      │  │   Serving      │  │  │
│  │  │   /ws           │  │   /health        │  │   /            │  │  │
│  │  │                 │  │   /api/models    │  │                │  │  │
│  │  │  • Accept conn  │  │   /api/models/   │  │                │  │  │
│  │  │  • Send/Receive │  │     load         │  │                │  │  │
│  │  │  • Manage state │  │                  │  │                │  │  │
│  │  └─────────────────┘  └──────────────────┘  └────────────────┘  │  │
│  │                                                                   │  │
│  │  ┌───────────────────────────────────────────────────────────┐  │  │
│  │  │            Connection Manager                             │  │  │
│  │  │  • Track active WebSocket connections                     │  │  │
│  │  │  • Broadcast messages                                     │  │  │
│  │  │  • Handle disconnections                                  │  │  │
│  │  └───────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │                              │ HTTP POST                          │  │
│  │                              ▼                                    │  │
│  │  ┌───────────────────────────────────────────────────────────┐  │  │
│  │  │          Ollama Query Handler                             │  │  │
│  │  │  • Format prompts with system context                     │  │  │
│  │  │  • Configure parameters (temp, top_p, top_k)              │  │  │
│  │  │  • Send to Ollama API                                     │  │  │
│  │  │  • Process responses                                      │  │  │
│  │  └───────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                    Port: 8081 (external) → 8000 (internal)              │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
                            HTTP REST API
                    (http://ollama:11434/api/generate)
                                   │
┌──────────────────────────────────▼───────────────────────────────────────┐
│                       Docker Container: ollama                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Ollama Service                               │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │                   REST API Server                           │ │  │
│  │  │   • /api/generate  - Generate text from prompt              │ │  │
│  │  │   • /api/pull      - Download models                        │ │  │
│  │  │   • /api/list      - List available models                  │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │                   Model Manager                             │ │  │
│  │  │   • Load models into memory                                 │ │  │
│  │  │   • Manage model lifecycle                                  │ │  │
│  │  │   • Handle concurrent requests                              │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │               AI Models (LLM Inference)                     │ │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │  │
│  │  │  │ Gemma 2B │  │  Phi-3   │  │ Llama    │  │  Qwen    │   │ │  │
│  │  │  │ 1.7 GB   │  │  2.3 GB  │  │ 3.2 1B   │  │ 2.5 1.5B │   │ │  │
│  │  │  │          │  │          │  │  1.3 GB  │  │  934 MB  │   │ │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  │                                                                   │  │
│  │  Memory Allocation: 8GB limit, 6GB reserved                      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                         Port: 11434                                      │
│                Volume: ollama_data (persistent model storage)            │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                    Docker Network: websockets_default                    │
│             (Internal communication between containers)                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

**1. Frontend (User Interface)**
- HTML/CSS/JavaScript single-page application
- WebSocket client for real-time communication
- Model selection dropdown
- Message display with typing indicators
- Connection status monitoring

**2. FastAPI Backend**
- WebSocket endpoint (`/ws`) for real-time chat
- REST API for model management
- Connection manager for multiple clients
- Request/response formatting
- Error handling and validation

**3. Ollama Engine**
- LLM model hosting and inference
- REST API for text generation
- Model management (pull, list, run)
- Memory-efficient model loading
- Concurrent request handling

### Data Flow

```
┌─────────┐                      ┌──────────┐                    ┌─────────┐
│ Browser │──── WebSocket ────▶│  FastAPI │──── HTTP POST ────▶│ Ollama  │
│         │                      │          │                    │         │
│  User   │◀─── WebSocket ─────│  Server  │◀─── Response ──────│  LLM    │
│   UI    │     (real-time)     │          │     (JSON)         │ Engine  │
└─────────┘                      └──────────┘                    └─────────┘
     │                                │                               │
     │                                │                               │
  Static                         app.py                          Models
  Files                         Python                          (AI)
```

### Message Flow Sequence

1. **User Input** → User types message and clicks Send
2. **WebSocket Send** → Message sent to FastAPI via WebSocket
3. **Prompt Formatting** → FastAPI formats prompt with system context
4. **HTTP Request** → FastAPI sends POST to Ollama API
5. **Model Inference** → Ollama processes prompt with selected LLM
6. **Response Generation** → AI generates response text
7. **JSON Response** → Ollama returns JSON to FastAPI
8. **WebSocket Send** → FastAPI forwards response via WebSocket
9. **UI Update** → Browser displays AI response in chat

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, Vanilla JS | User interface |
| **Communication** | WebSockets | Real-time bidirectional messaging |
| **Backend Framework** | FastAPI (Python) | API server & WebSocket handler |
| **AI Engine** | Ollama | LLM hosting and inference |
| **Models** | Gemma, Phi-3, Llama, Qwen | Language models |
| **Containerization** | Docker + Docker Compose | Deployment & orchestration |
| **Networking** | Docker Network | Container communication |
| **Storage** | Docker Volumes | Persistent model storage |

## Configuration

### Environment Variables

All configuration is done through the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `FASTAPI_HOST` | FastAPI server host | `0.0.0.0` |
| `FASTAPI_PORT` | FastAPI server port (internal) | `8000` |
| `FASTAPI_EXTERNAL_PORT` | FastAPI external port | `8000` |
| `OLLAMA_HOST` | Ollama API URL | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model to use | `llama2` |
| `OLLAMA_TIMEOUT` | Request timeout in seconds | `120` |
| `OLLAMA_EXTERNAL_PORT` | Ollama external port | `11434` |

### Change the AI Model

Simply update the `OLLAMA_MODEL` variable in your `.env` file:

```bash
OLLAMA_MODEL=mistral
```

Then restart the services:

```bash
docker-compose down
docker-compose up --build
```

Available models: `llama2`, `mistral`, `codellama`, `phi`, etc.
See [Ollama library](https://ollama.ai/library) for more models.

### Adjust Ports

Update port numbers in your `.env` file:

```bash
FASTAPI_EXTERNAL_PORT=3000  # Access app on port 3000
OLLAMA_EXTERNAL_PORT=11435  # Ollama on port 11435
```

## API Endpoints

- `GET /` - Serves the chat interface
- `WebSocket /ws` - WebSocket endpoint for real-time chat
- `GET /health` - Health check endpoint
- `GET /api/models` - List available AI models
- `POST /api/models/load` - Load/switch to a different model

## Troubleshooting

### Ollama not responding

```bash
# Check if Ollama is running
docker ps

# View Ollama logs
docker logs ollama

# Restart services
docker-compose restart
```

### Model not downloaded

```bash
# Manually pull the model
docker exec -it ollama ollama pull llama2
```

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Or change the port in docker-compose.yml
```

## Development

### Run locally without Docker

1. Install Ollama locally: https://ollama.ai/download

2. Create a `.env` file with local configuration:
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

3. Pull the model:
```bash
ollama pull llama2
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

5. Run the FastAPI server:
```bash
uvicorn app:app --reload
```

6. Access at `http://localhost:8000`

## Technologies Used

- **FastAPI**: Modern Python web framework
- **WebSockets**: Real-time bidirectional communication
- **Ollama**: Local LLM runtime
- **Llama2**: Meta's open-source language model
- **Docker**: Containerization
- **Vanilla JavaScript**: No frontend frameworks needed

## License

This is a POC/educational project. Feel free to use and modify as needed.

## Next Steps

Potential enhancements:
- Add conversation history
- Support multiple concurrent users
- Implement streaming responses
- Add user authentication
- Store chat history in database
- Add model selection in UI
- Implement rate limiting
- Add message formatting (markdown support)

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
