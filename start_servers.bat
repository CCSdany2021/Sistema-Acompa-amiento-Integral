@echo off
echo ==========================================
echo Starting SISTEMA DE ACOMPAÑAMIENTO INTEGRAL
echo ==========================================

echo [1/2] Starting Database Server (Node.js on Port 8000)...
start "DB-Server-Node" cmd /k "cd /d c:\Sistema_reporte_academico\server && npm start"

echo [2/2] Starting Main Application (Python on Port 8001)...
start "App-Server-Python" cmd /k "cd /d c:\Sistema_acompañamiento_integral && set PGCLIENTENCODING=UTF8 && set LC_MESSAGES=Spanish_Colombia.1252 && .\venv\Scripts\activate && python -m src.main"

echo.
echo Both servers are starting in separate windows.
echo Please wait a few seconds for them to initialize.
echo.
echo Application: http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo.
pause
