#!/bin/bash
# Demo script for Text Summarizer CLI Tool

echo "=============================================="
echo "Text Summarizer CLI Tool - Demo"
echo "=============================================="
echo

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this demo from the TextSummarizer directory"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "1. Testing local mode (no API key required):"
echo "   Command: $PYTHON_CMD main.py --file sample_text.txt --model local --no-save --verbose"
echo
$PYTHON_CMD main.py --file sample_text.txt --model local --no-save --verbose

echo
echo "=============================================="
echo

echo "2. Testing direct text input:"
echo "   Command: $PYTHON_CMD main.py --text \"This is a sample text...\" --model local --no-save"
echo
$PYTHON_CMD main.py --text "This is a sample text about artificial intelligence and machine learning. It covers various applications including natural language processing, computer vision, and robotics. The text discusses the current state of AI technology, its potential benefits, and future challenges. Key areas of development include autonomous vehicles, medical diagnosis, and smart home systems. Researchers are working on improving AI safety and ensuring ethical deployment of these technologies." --model local --no-save

echo
echo "=============================================="
echo

echo "3. Testing stdin input:"
echo "   Command: echo \"Short text...\" | $PYTHON_CMD main.py --model local --no-save"
echo
echo "Technology is rapidly evolving in the 21st century. Smartphones have become ubiquitous, connecting people globally. Social media platforms enable instant communication. Cloud computing provides scalable infrastructure. Artificial intelligence is automating various tasks. These developments are transforming how we work, learn, and interact." | $PYTHON_CMD main.py --model local --no-save

echo
echo "=============================================="
echo

echo "4. Testing configuration setup:"
echo "   Command: $PYTHON_CMD main.py --setup"
echo
echo "Note: This will show configuration options. You can set up API keys for better AI models."
echo

echo "=============================================="
echo "Demo completed!"
echo
echo "Next steps:"
echo "1. Set up API keys for OpenAI or Anthropic for better results"
echo "2. Try: $PYTHON_CMD main.py --file sample_text.txt --model openai"
echo "3. Read README.md for more usage examples"
echo "=============================================="