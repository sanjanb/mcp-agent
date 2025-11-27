#!/bin/bash
echo "HR Agent MCP Project - Quick Start"
echo "==================================="

echo ""
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Running setup script..."
python setup.py

echo ""
echo "Setup complete!"
echo ""
echo "To start the HR Assistant Agent:"
echo "1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
echo "2. Run: streamlit run ui/streamlit_app.py"
echo ""