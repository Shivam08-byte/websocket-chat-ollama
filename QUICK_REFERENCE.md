# 🚀 Quick Reference - WebSocket Chat

## Access
```
http://localhost:8081
```

## Start/Stop
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f
```

## Verify System
```bash
./verify.sh
```

## Common Commands
```bash
# Check containers
docker ps

# Check health
curl http://localhost:8081/health

# Check models
curl http://localhost:8081/api/models

# List Ollama models
docker exec ollama ollama list

# Pull a model manually
docker exec ollama ollama pull gemma:2b

# View specific logs
docker logs fastapi_websocket
docker logs ollama
```

## Configuration
Edit `.env` file to customize:
- `FASTAPI_EXTERNAL_PORT=8081` - Change access port
- `OLLAMA_MODEL=gemma:2b` - Change default model

## Troubleshooting
```bash
# Port in use? Change in .env:
FASTAPI_EXTERNAL_PORT=3000

# Out of memory? Use smaller model:
OLLAMA_MODEL=qwen2.5:1.5b

# Restart everything:
docker-compose down && docker-compose up -d --build

# Check Docker memory:
# Docker Desktop → Settings → Resources → Memory → 8GB+
```

## Available Models
- **gemma:2b** (1.7 GB) - Default, balanced
- **phi3** (2.3 GB) - Best reasoning
- **llama3.2:1b** (1.3 GB) - Fastest
- **qwen2.5:1.5b** (934 MB) - Smallest

## Documentation
- **SETUP.md** - Complete setup guide
- **README.md** - Project overview
- **PROJECT_SUMMARY.md** - Full details
- **MODEL_SELECTION.md** - Model info

## Support
Run verification: `./verify.sh`
Check logs: `docker logs <container_name>`
See SETUP.md for detailed troubleshooting

---
✅ All systems operational!
🎉 Start chatting at http://localhost:8081
