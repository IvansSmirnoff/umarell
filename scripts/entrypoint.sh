#!/bin/bash
# Ollama entrypoint wrapper
# Starts Ollama server and runs initialization

set -e

echo "🚀 Starting Ollama service..."

# Start Ollama server in the background
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama API to be ready..."
until ollama list >/dev/null 2>&1; do
    sleep 1
done
echo "✅ Ollama API is ready!"

# Run initialization script
if [ -f "/scripts/init_ollama.sh" ]; then
    echo "🔧 Running initialization..."
    bash /scripts/init_ollama.sh
else
    echo "⚠️  Initialization script not found, skipping setup"
fi

echo ""
echo "✅ Ollama is fully operational!"
echo ""

# Keep the container running by waiting for the Ollama process
wait $OLLAMA_PID
