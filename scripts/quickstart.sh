#!/bin/bash
# Quick Start Script for Project Umarell
# Run this on your VPS after copying all files

set -e

echo "🏗️  Project Umarell - Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create .env from config/.env.example and configure your InfluxDB settings:"
    echo "  cp config/.env.example .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

echo "✅ Found .env file"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create necessary directories
mkdir -p ollama_data

echo "📁 Created data directories"
echo ""

# Start the stack
echo "🚀 Starting Docker containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check services
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Base services started!"
echo ""
echo "🤖 Ollama is now setting up models automatically..."
echo "   (First launch only - this takes 10-20 minutes)"
echo ""
echo "   Watch the setup progress:"
echo "   docker compose logs -f ollama"
echo ""
echo "Next steps:"
echo ""
echo "1. Wait for Ollama setup to complete (watch logs above)"
echo ""
echo "2. Access Open WebUI at:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "3. Install the umarell_tool.py in Open WebUI:"
echo "   Settings → Tools → + Add Tool → Paste src/umarell_tool.py"
echo ""
echo "4. Select 'umarell' model and start chatting!"
echo ""
echo "📝 View all logs:  docker compose logs -f"
echo "🛑 Stop all:       docker compose down"
echo "📊 Check status:   ./scripts/check_status.sh"
echo "📖 Documentation:  docs/README.md"
echo ""
