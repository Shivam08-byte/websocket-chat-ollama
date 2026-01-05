# Complete Setup Guide - WebSocket Chat with Ollama

This guide will help you set up the WebSocket Chat application on **any device** (Windows, macOS, Linux).

## 📋 Prerequisites

### Required Software
1. **Docker Desktop**
   - [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - [Download for macOS](https://docs.docker.com/desktop/install/mac-install/)
   - [Download for Linux](https://docs.docker.com/desktop/install/linux-install/)

2. **Git** (optional, for cloning)
   - [Download Git](https://git-scm.com/downloads)

### System Requirements
- **RAM**: Minimum 8GB (12GB recommended)
- **Storage**: 10GB free space for models
- **Internet**: Required for initial download

### Docker Memory Configuration
**Important**: Increase Docker's memory allocation:

#### Windows/macOS:
1. Open Docker Desktop
2. Go to Settings → Resources → Memory
3. Set to **8GB or higher**
4. Click "Apply & Restart"

#### Linux:
Docker uses system memory by default, no configuration needed.

---

## 🚀 Step-by-Step Setup

### Step 1: Get the Project Files

#### Option A: Clone with Git
```bash
git clone <repository-url>
cd websockets
```

#### Option B: Download ZIP
1. Download the project ZIP file
2. Extract it to your desired location
3. Open terminal/command prompt in that folder

### Step 2: Configure Environment

Copy the example environment file:

**macOS/Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

#### Environment Variables (`.env` file)
```env
# Application Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=gemma:2b
OLLAMA_TIMEOUT=120

# Docker Ports
FASTAPI_EXTERNAL_PORT=8081
OLLAMA_EXTERNAL_PORT=11434
```

**Customize if needed:**
- `FASTAPI_EXTERNAL_PORT` - Change if port 8081 is already in use
- `OLLAMA_MODEL` - Default model to load (gemma:2b, phi3, llama3.2:1b, qwen2.5:1.5b)

### Step 3: Start the Application

Run the following command in your terminal:

**All Platforms:**
```bash
docker-compose up -d --build
```

**What happens:**
1. Downloads Docker images (~2-3 minutes)
2. Builds FastAPI container (~1 minute)
3. Downloads default AI model (~2-5 minutes)
4. Starts both services

**First-time setup takes 5-10 minutes total.**

### Step 4: Verify Installation

Check if containers are running:
```bash
docker ps
```

You should see:
- `ollama` - Running on port 11434
- `fastapi_websocket` - Running on port 8081

Test the health endpoint:
```bash
curl http://localhost:8081/health
```

### Step 5: Access the Chat

Open your browser and navigate to:
```
http://localhost:8081
```

You should see the chat interface with a model selector dropdown!

---

## 🎯 Using the Application

### Chatting with AI
1. Type your message in the input box
2. Press Enter or click "Send"
3. Wait for AI response (usually 2-10 seconds)

### Switching Models
1. Click the model dropdown in the top-right corner
2. Select your desired model
3. Wait for "loaded successfully" message (first-time only)
4. Start chatting!

### Available Models
| Model | Size | Best For |
|-------|------|----------|
| **Gemma 2B** | 1.7 GB | General conversations, balanced |
| **Phi-3 Mini** | 2.3 GB | Reasoning, technical questions |
| **Llama 3.2 1B** | 1.3 GB | Fast responses, lightweight |
| **Qwen 2.5 1.5B** | 934 MB | Multilingual support |

---

## 🔧 Common Issues & Solutions

### Issue 1: Port Already in Use
**Error:** `Bind for 0.0.0.0:8081 failed: port is already allocated`

**Solution:** Change the port in `.env`:
```env
FASTAPI_EXTERNAL_PORT=3000  # Or any available port
```
Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Issue 2: Out of Memory
**Error:** `llama runner process has terminated: signal: killed`

**Solution:** Increase Docker memory allocation (see Prerequisites) or use a smaller model:
```env
OLLAMA_MODEL=qwen2.5:1.5b  # Smallest model
```

### Issue 3: Model Loading Fails
**Error:** Model fails to download

**Solution:** Check internet connection and retry:
```bash
docker exec ollama ollama pull gemma:2b
```

### Issue 4: Cannot Access http://localhost:8081
**Solutions:**
- Try `http://127.0.0.1:8081` instead
- Check if containers are running: `docker ps`
- View logs: `docker logs fastapi_websocket`
- Restart: `docker-compose restart`

### Issue 5: WebSocket Connection Error
**Solution:** 
- Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Try a different browser

---

## 📦 Pre-loading All Models (Optional)

To download all models at once for instant switching:

**macOS/Linux:**
```bash
chmod +x pull-all-models.sh
./pull-all-models.sh
```

**Windows (Git Bash):**
```bash
bash pull-all-models.sh
```

**Windows (PowerShell/CMD):**
```bash
docker exec ollama ollama pull gemma:2b
docker exec ollama ollama pull phi3
docker exec ollama ollama pull llama3.2:1b
docker exec ollama ollama pull qwen2.5:1.5b
```

**Download time:** ~10-15 minutes  
**Total size:** ~6-8 GB

---

## 🛑 Stopping the Application

### Stop services (keeps data):
```bash
docker-compose down
```

### Stop and remove all data:
```bash
docker-compose down -v
```

### Restart services:
```bash
docker-compose restart
```

---

## 🔍 Viewing Logs

### View all logs:
```bash
docker-compose logs -f
```

### View specific service logs:
```bash
docker logs ollama
docker logs fastapi_websocket
```

### View last 50 lines:
```bash
docker logs --tail 50 fastapi_websocket
```

---

## 🌐 Accessing from Other Devices on Network

To access from other devices on your local network:

1. Find your computer's IP address:

**macOS/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
ipconfig
```

2. On other devices, open browser to:
```
http://YOUR_IP_ADDRESS:8081
```

Example: `http://192.168.1.100:8081`

**Note:** Ensure your firewall allows incoming connections on port 8081.

---

## 🔄 Updating the Application

### Pull latest changes:
```bash
git pull
# or download new ZIP and replace files
```

### Rebuild containers:
```bash
docker-compose down
docker-compose up -d --build
```

---

## 📊 Resource Usage

**Typical Resource Usage:**
- **Gemma 2B:** ~2-3 GB RAM
- **Phi-3:** ~3-4 GB RAM
- **Llama 3.2 1B:** ~1.5-2 GB RAM
- **Qwen 2.5 1.5B:** ~1-1.5 GB RAM

**Disk Space:**
- Docker images: ~2 GB
- Models (all): ~6-8 GB
- Total: ~10 GB

---

## 🧹 Cleanup

### Remove containers:
```bash
docker-compose down
```

### Remove containers and volumes (deletes models):
```bash
docker-compose down -v
```

### Remove Docker images:
```bash
docker rmi websockets-fastapi
docker rmi ollama/ollama
```

### Full cleanup:
```bash
docker-compose down -v
docker system prune -a
```

---

## 🆘 Getting Help

### Check application health:
```bash
curl http://localhost:8081/health
```

### List available models:
```bash
curl http://localhost:8081/api/models
```

### Test Ollama directly:
```bash
docker exec ollama ollama list
docker exec ollama ollama run gemma:2b "Hello!"
```

### System information:
```bash
docker --version
docker-compose --version
docker info
```

---

## ✅ Verification Checklist

Before using, verify:

- [ ] Docker Desktop is running
- [ ] Docker has 8GB+ memory allocated
- [ ] Both containers are running (`docker ps`)
- [ ] Health endpoint responds (`curl http://localhost:8081/health`)
- [ ] Can access http://localhost:8081 in browser
- [ ] Model dropdown loads with 4 models
- [ ] Can send messages and receive responses
- [ ] Can switch between models

---

## 🎓 Next Steps

Once everything is working:

1. **Try different models** - Test each model's strengths
2. **Experiment with queries** - Ask technical, creative, or general questions
3. **Monitor resources** - Use `docker stats` to see resource usage
4. **Customize** - Modify `.env` for your needs
5. **Share** - Access from other devices on your network

---

## 📝 File Structure Reference

```
websockets/
├── app.py                      # FastAPI backend
├── requirements.txt            # Python dependencies
├── Dockerfile                  # FastAPI container config
├── docker-compose.yml          # Service orchestration
├── .env                        # Your configuration (create from .env.example)
├── .env.example                # Template configuration
├── .gitignore                  # Git ignore rules
├── .dockerignore               # Docker ignore rules
├── README.md                   # Project overview
├── SETUP.md                    # This setup guide
├── MODEL_SELECTION.md          # Model selection feature docs
├── pull-all-models.sh          # Script to pre-load all models
├── pull-model.sh               # Script for single model
└── static/
    ├── index.html              # Chat UI
    ├── style.css               # Styling
    └── script.js               # WebSocket client
```

---

## 🌟 Success!

If you've reached this point and everything works, congratulations! 🎉

You now have a fully functional AI chat application with:
- Real-time WebSocket communication
- Multiple AI models to choose from
- Modern, responsive interface
- Complete Docker containerization

Enjoy chatting with AI! 🤖💬
