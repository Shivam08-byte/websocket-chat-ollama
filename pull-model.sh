#!/bin/bash

# Script to pull the Ollama model after containers are started

echo "Waiting for Ollama service to be ready..."
sleep 10

echo "Pulling model: ${OLLAMA_MODEL:-llama2}"
docker exec ollama ollama pull ${OLLAMA_MODEL:-llama2}

echo "Model pulled successfully!"
