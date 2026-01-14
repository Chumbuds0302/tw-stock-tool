@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

:: Kill any process running on port 8501 to avoid port incrementing
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo Starting Streamlit App...
streamlit run app.py --server.port 8501
