#!/bin/bash

# Script to pre-pull recommended models

echo "🚀 Pre-pulling recommended AI models..."
echo "This will download multiple models (~6-8 GB total)"
echo ""

MODELS=("gemma:2b" "phi3" "llama3.2:1b" "qwen2.5:1.5b")

for model in "${MODELS[@]}"; do
    echo "📦 Pulling $model..."
    docker exec ollama ollama pull "$model"
    
    if [ $? -eq 0 ]; then
        echo "✅ $model downloaded successfully"
    else
        echo "❌ Failed to download $model"
    fi
    echo ""
done

echo "🎉 Model pre-loading complete!"
echo "Available models:"
docker exec ollama ollama list
