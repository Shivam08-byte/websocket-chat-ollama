#!/bin/bash

# Verification script for WebSocket Chat setup

echo "🔍 WebSocket Chat - System Verification"
echo "========================================"
echo ""

# Check Docker
echo "1️⃣  Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker installed: $(docker --version)"
else
    echo "   ❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

# Check Docker Compose
echo ""
echo "2️⃣  Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✅ Docker Compose installed: $(docker-compose --version)"
else
    echo "   ❌ Docker Compose not found."
    exit 1
fi

# Check if Docker daemon is running
echo ""
echo "3️⃣  Checking Docker daemon..."
if docker info &> /dev/null; then
    echo "   ✅ Docker daemon is running"
else
    echo "   ❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Check if containers are running
echo ""
echo "4️⃣  Checking containers..."
OLLAMA_RUNNING=$(docker ps --filter "name=ollama" --format "{{.Names}}" 2>/dev/null)
FASTAPI_RUNNING=$(docker ps --filter "name=fastapi" --format "{{.Names}}" 2>/dev/null)

if [ -n "$OLLAMA_RUNNING" ]; then
    echo "   ✅ Ollama container is running"
else
    echo "   ❌ Ollama container not running. Run: docker-compose up -d"
fi

if [ -n "$FASTAPI_RUNNING" ]; then
    echo "   ✅ FastAPI container is running"
else
    echo "   ❌ FastAPI container not running. Run: docker-compose up -d"
fi

# Check if .env exists
echo ""
echo "5️⃣  Checking configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
else
    echo "   ⚠️  .env file not found. Run: cp .env.example .env"
fi

# Check health endpoint
echo ""
echo "6️⃣  Checking API health..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ API is healthy (HTTP 200)"
        HEALTH=$(curl -s http://localhost:8081/health)
        echo "   📊 $HEALTH"
    else
        echo "   ❌ API not responding (HTTP $HTTP_CODE)"
    fi
else
    echo "   ⚠️  curl not installed, skipping health check"
fi

# Check models API
echo ""
echo "7️⃣  Checking models API..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/models 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Models API is working"
    else
        echo "   ❌ Models API not responding"
    fi
fi

# Check available models in Ollama
echo ""
echo "8️⃣  Checking available models..."
if [ -n "$OLLAMA_RUNNING" ]; then
    MODELS=$(docker exec ollama ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$MODELS" -gt 0 ]; then
        echo "   ✅ Found $MODELS model(s) in Ollama"
        echo ""
        docker exec ollama ollama list | head -n 6
    else
        echo "   ⚠️  No models found. Models will be pulled on first use."
    fi
fi

# Summary
echo ""
echo "========================================"
echo "📋 Verification Summary"
echo "========================================"

if [ -n "$OLLAMA_RUNNING" ] && [ -n "$FASTAPI_RUNNING" ] && [ "$HTTP_CODE" = "200" ]; then
    echo "✅ All systems operational!"
    echo ""
    echo "🎉 You can now access the chat at:"
    echo "   👉 http://localhost:8081"
    echo ""
else
    echo "⚠️  Some issues detected. Please review the checks above."
    echo ""
    echo "📖 For help, see:"
    echo "   • SETUP.md for detailed setup instructions"
    echo "   • README.md for project overview"
    echo ""
fi
