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

:: 1. Iniciar Sistema Gestor Educativo (Django - Puerto 8000) - Si no está ya corriendo
echo  [1/2] Verificando Sistema Gestor Educativo (Puerto 8000)...
:: Nota: Sistema_gestor_educativo debe estar corriendo en su propia ventana/servicio

:: 2. Iniciar Aplicación Principal (Python/FastAPI)
echo  [2/2] Levantando Aplicacion SAI (Puerto 8005)...
set PGCLIENTENCODING=UTF8
set LC_MESSAGES=Spanish_Colombia.1252
start "SAI - Frontend/App (Python)" cmd /k "cd /d c:\Sistema_acompañamiento_integral && .\venv\Scripts\activate && python -m src.main"

echo.
echo  ==========================================================
echo   TODO LISTO:
echo.
echo   - Sistema Gestor Educativo: http://localhost:8000
echo   - App SAI: http://localhost:8005
echo   - API Docs: http://localhost:8005/docs
echo.
echo   IMPORTANTE: Asegúrate que Sistema_gestor_educativo esté
echo   corriendo en su propia ventana ANTES de iniciar SAI.
echo.
echo   Presione cualquier tecla para cerrar esta ventana del lanzador.
echo   (Los servidores seguiran corriendo en sus ventanas propias).
echo  ==========================================================
echo.
pause > nul
exit
