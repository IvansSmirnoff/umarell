#!/bin/bash
# Check Umarell setup status

echo "🔍 Project Umarell - Setup Status Check"
echo "========================================"
echo ""

# Check if containers are running
echo "📦 Container Status:"
docker compose ps
echo ""

# Check if Ollama is responding
echo "🤖 Ollama Status:"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "   ✅ Ollama API is responding"
    
    # Check installed models
    echo ""
    echo "📚 Installed Models:"
    docker exec ollama ollama list
    
    # Check for specific models
    echo ""
    echo "🎯 Required Models:"
    
    if docker exec ollama ollama list | grep -q "qwen2.5:7b"; then
        echo "   ✅ qwen2.5:7b (The Brain)"
    else
        echo "   ❌ qwen2.5:7b (Missing - still downloading?)"
    fi
    
    if docker exec ollama ollama list | grep -q "qwen2.5-coder:1.5b"; then
        echo "   ✅ qwen2.5-coder:1.5b (The Tool User)"
    else
        echo "   ❌ qwen2.5-coder:1.5b (Missing - still downloading?)"
    fi
    
    if docker exec ollama ollama list | grep -q "umarell"; then
        echo "   ✅ umarell (L'Umarell persona) - READY!"
    else
        echo "   ❌ umarell (Missing - check logs)"
    fi
    
    # Check setup marker
    echo ""
    echo "🏁 Setup Completion:"
    if docker exec ollama test -f /root/.ollama/.umarell_setup_complete; then
        echo "   ✅ Setup marker found - fully configured"
    else
        echo "   ⏳ Setup in progress or not started"
        echo "   💡 Watch logs: docker compose logs -f ollama"
    fi
    
else
    echo "   ❌ Ollama API is not responding"
    echo "   💡 Check if container is running: docker compose ps"
fi

echo ""
echo "🌐 Service URLs:"
echo "   Open WebUI:  http://localhost:8080"
echo "   Neo4j:       http://localhost:7474"
echo "   Ollama API:  http://localhost:11434"
echo ""

# Check Neo4j
echo "🗄️  Neo4j Status:"
if curl -s http://localhost:7474 >/dev/null 2>&1; then
    echo "   ✅ Neo4j is responding"
else
    echo "   ❌ Neo4j is not responding"
fi

echo ""
echo "💡 Useful Commands:"
echo "   View Ollama logs:  docker compose logs -f ollama"
echo "   Restart services:  docker compose restart"
echo "   Stop all:          docker compose down"
echo "   Fresh start:       docker compose down && docker compose up -d"
echo ""
