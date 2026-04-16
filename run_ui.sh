#!/bin/bash
"""
Launch script for TextSummarizer Web Interface

This script starts the Streamlit web application for TextSummarizer.
Usage: ./run_ui.sh
"""

echo "🚀 Starting TextSummarizer Web Interface..."
echo "📝 Open your browser to the URL that appears below"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

# Start Streamlit
streamlit run app.py --server.headless true --server.port 8501

echo ""
echo "✅ TextSummarizer Web Interface stopped"