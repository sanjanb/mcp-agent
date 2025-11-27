@echo off
echo HR Agent MCP Project - Quick Start
echo ===================================

echo.
echo Setting up Python environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Running setup script...
python setup.py

echo.
echo Setup complete! 
echo.
echo To start the HR Assistant Agent:
echo 1. Set your OpenAI API key: set OPENAI_API_KEY=your-key-here
echo 2. Run: streamlit run ui/streamlit_app.py
echo.
pause