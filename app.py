import os
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List

app = FastAPI(title="WebSocket Chat with Ollama")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get configuration from environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

# Current active model (can be changed via API)
current_model = OLLAMA_MODEL

# Available models with descriptions
AVAILABLE_MODELS = {
    "gemma:2b": {
        "name": "Gemma 2B",
        "size": "1.7 GB",
        "description": "Google's efficient model, great for general conversations"
    },
    "phi3": {
        "name": "Phi-3 Mini",
        "size": "2.3 GB", 
        "description": "Microsoft's small model, excellent reasoning capabilities"
    },
    "llama3.2:1b": {
        "name": "Llama 3.2 1B",
        "size": "1.3 GB",
        "description": "Meta's compact model, fast and efficient"
    },
    "qwen2.5:1.5b": {
        "name": "Qwen 2.5 1.5B",
        "size": "934 MB",
        "description": "Alibaba's multilingual model, supports many languages"
    }
}

# Active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()


async def query_ollama(prompt: str) -> str:
    """Query Ollama API and return response"""
    try:
        # Create a better system prompt for more focused responses
        system_prompt = "You are a helpful AI assistant. Provide clear, concise, and accurate responses. Keep your answers brief and to the point."
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": current_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 200,  # Limit response length
                        "stop": ["\nUser:", "User:", "\n\n\n"]  # Stop at reasonable points
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "No response from model")
                # Clean up the response
                response_text = response_text.strip()
                return response_text if response_text else "I'm sorry, I couldn't generate a proper response."
            else:
                return f"Error: Received status code {response.status_code}"
                
    except httpx.ConnectError:
        return "Error: Cannot connect to Ollama. Make sure Ollama service is running."
    except Exception as e:
        return f"Error: {str(e)}"


@app.get("/")
async def get():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat communication"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_message(
            json.dumps({
                "type": "system",
                "message": "Connected to chat server. Type your message to chat with the AI."
            }),
            websocket
        )
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if not user_message.strip():
                    continue
                
                # Echo user message
                await manager.send_message(
                    json.dumps({
                        "type": "user",
                        "message": user_message
                    }),
                    websocket
                )
                
                # Send typing indicator
                await manager.send_message(
                    json.dumps({
                        "type": "typing",
                        "message": "AI is typing..."
                    }),
                    websocket
                )
                
                # Get AI response
                ai_response = await query_ollama(user_message)
                
                # Send AI response
                await manager.send_message(
                    json.dumps({
                        "type": "ai",
                        "message": ai_response
                    }),
                    websocket
                )
                
            except json.JSONDecodeError:
                await manager.send_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid message format"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ollama_host": OLLAMA_HOST,
        "ollama_model": current_model,
        "ollama_timeout": OLLAMA_TIMEOUT
    }


@app.get("/api/models")
async def get_available_models():
    """Get list of available models"""
    return {
        "current_model": current_model,
        "available_models": AVAILABLE_MODELS
    }


@app.post("/api/models/load")
async def load_model(model_data: dict):
    """Load a specific model"""
    global current_model
    
    model_name = model_data.get("model")
    
    if not model_name or model_name not in AVAILABLE_MODELS:
        return {
            "success": False,
            "message": f"Invalid model. Available models: {', '.join(AVAILABLE_MODELS.keys())}"
        }
    
    try:
        # Check if model is already pulled
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Pull the model if not available
            pull_response = await client.post(
                f"{OLLAMA_HOST}/api/pull",
                json={"name": model_name}
            )
            
            if pull_response.status_code == 200:
                current_model = model_name
                return {
                    "success": True,
                    "message": f"Model {model_name} loaded successfully",
                    "current_model": current_model
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to load model: {pull_response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Error loading model: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)
