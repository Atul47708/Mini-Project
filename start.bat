@echo off
title Multimodal AI Companion Launcher
cd /d "%~dp0"

echo ========================================================
echo 1/2. Starting Backend Server (FastAPI on port 8000)...
echo ========================================================
start "AI Companion - Backend" cmd /k python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

echo Waiting for backend server to initialize...
ping -n 5 127.0.0.1 >nul

echo ========================================================
echo 2/2. Starting Frontend UI (Streamlit on port 8501)...
echo ========================================================
start "AI Companion - Frontend" cmd /k python -m streamlit run frontend\app.py

echo.
echo ========================================================
echo Both servers running!
echo - Frontend UI:  http://localhost:8501
echo - Backend Docs: http://127.0.0.1:8000/docs
echo ========================================================
