#!/bin/bash
set -e

echo "🏗️  Setting up Project Umarell - The Grumpy Building Inspector"
echo "============================================================="

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
until sudo docker exec ollama ollama list >/dev/null 2>&1; do
    echo "   Ollama not ready yet, waiting 2 seconds..."
    sleep 2
done
echo "✅ Ollama is ready!"

# Pull the brain model (Umarell's personality)
echo ""
echo "🧠 Pulling qwen2.5:7b (The Brain - Umarell's personality)..."
sudo docker exec ollama ollama pull qwen2.5:7b

# Pull the tool user model (generates queries)
echo ""
echo "🔧 Pulling qwen2.5-coder:1.5b (The Tool User - query generator)..."
sudo docker exec ollama ollama pull qwen2.5-coder:1.5b

# Create the custom Umarell model
echo ""
echo "👴 Creating custom 'umarell' model with Milanese attitude..."
sudo docker exec ollama ollama create umarell -f /modelfiles/Modelfile_Umarell

echo ""
echo "✅ Setup complete!"
echo ""
echo "L'Umarell says: 'Taaac! Everything is ready. Now let's see if you know how to use it, barlafus!'"
echo ""
echo "Next steps:"
echo "  1. Configure your .env file with InfluxDB credentials"
echo "  2. Access Open WebUI at http://localhost:8080"
echo "  3. Select the 'umarell' model in the chat"
echo "  4. Install the umarell_tool.py in Open WebUI Tools section"
echo ""
