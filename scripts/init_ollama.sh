#!/bin/bash
# Ollama initialization script
# This runs when the Ollama container starts and sets up models if needed

set -e

SETUP_MARKER="/root/.ollama/.umarell_setup_complete"

echo "🏗️  Umarell Initialization Check"
echo "================================="

# Check if setup has already been completed
if [ -f "$SETUP_MARKER" ]; then
    echo "✅ Umarell is already set up (found marker file)"
    echo "   Models installed:"
    ollama list
    echo ""
    echo "🎉 L'Umarell says: 'Va bene, I'm ready to inspect!'"
    exit 0
fi

echo "🆕 First time setup detected - Installing Umarell models..."
echo ""

# Check if qwen2.5:7b exists
if ollama list | grep -q "qwen2.5:7b"; then
    echo "✅ qwen2.5:7b already exists"
else
    echo "🧠 Pulling qwen2.5:7b (The Brain - 4.7GB, this may take a while)..."
    ollama pull qwen2.5:7b
fi

# Check if qwen2.5-coder:1.5b exists
if ollama list | grep -q "qwen2.5-coder:1.5b"; then
    echo "✅ qwen2.5-coder:1.5b already exists"
else
    echo "🔧 Pulling qwen2.5-coder:1.5b (The Tool User - 934MB)..."
    ollama pull qwen2.5-coder:1.5b
fi

# Check if umarell model exists
if ollama list | grep -q "umarell"; then
    echo "✅ umarell model already exists"
else
    echo "👴 Creating custom 'umarell' model with Milanese attitude..."
    if [ -f "/modelfiles/Modelfile_Umarell" ]; then
        ollama create umarell -f /modelfiles/Modelfile_Umarell
    else
        echo "⚠️  Warning: /modelfiles/Modelfile_Umarell not found!"
        echo "   Skipping umarell model creation"
        exit 1
    fi
fi

# Create marker file to indicate setup is complete
echo "✅ Creating setup marker file..."
touch "$SETUP_MARKER"

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "L'Umarell says: 'Taaac! Everything is ready. Now let's see if you know how to use it, barlafus!'"
echo ""
echo "Installed models:"
ollama list
echo ""
