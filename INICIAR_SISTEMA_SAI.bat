@echo off
TITLE Sistema de Acompañamiento Integral (SAI) 
COLOR 0B

:: ==========================================================
::     SISTEMA DE ACOMPAÑAMIENTO INTEGRAL (SAI)
::           LANZADOR INTEGRADO DE SERVIDORES
:: ==========================================================
echo.
echo  [+] Iniciando servidores para el SAI...
echo.

:: 1. Iniciar Servidor de Base de Datos (Node.js)
echo  [1/2] Levantando API de Datos Estudiantiles (Puerto 8000)...
start "SAI - API Datos (Node)" cmd /k "cd /d c:\Sistema_reportes_academicos && npm start"

:: 2. Iniciar Aplicación Principal (Python/FastAPI)
echo  [2/2] Levantando Aplicacion SAI (Puerto 8005)...
set PGCLIENTENCODING=UTF8
set LC_MESSAGES=Spanish_Colombia.1252
start "SAI - Frontend/App (Python)" cmd /k "cd /d c:\Sistema_acompañamiento_integral && python -m src.main"

echo.
echo  ==========================================================
echo   TODO LISTO:
echo.
echo   - App: http://localhost:8005
echo   - API: http://localhost:8005/docs (Documentacion)
echo.
echo   Presione cualquier tecla para cerrar esta ventana del lanzador.
echo   (Los servidores seguiran corriendo en sus ventanas propias).
echo  ==========================================================
echo.
pause > nul
exit
