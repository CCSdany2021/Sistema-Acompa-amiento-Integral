@echo off
TITLE Habilitar Acceso por Celular al SAI
COLOR 0A

echo ==========================================================
echo   SISTEMA DE ACOMPAÑAMIENTO INTEGRAL (SAI)
echo   Configuracion de Red para Celulares / Otros Equipos
echo ==========================================================
echo.
echo Esto abrira el puerto 8005 de tu compu para que el celular
echo se pueda conectar por Wi-Fi. Te pedira permisos de Administrador
echo en unos segundos...
echo.

:: Solicitar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Solicitando permisos de Administrador...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    echo [INFO] Permisos concedidos. Configuracion en curso...
    echo.
    :: Añadir regla de Firewall
    netsh advfirewall firewall add rule name="SAI Puerto 8005" dir=in action=allow protocol=TCP localport=8005 >nul
    
    echo ==========================================================
    echo  !LISTO! El permiso fue agregado correctamente al Firewall.
    echo ==========================================================
    echo.
    echo Ya puedes volver a darle doble clic a "INICIAR_SISTEMA_SAI.bat"
    echo e intentar entrar desde tu celular al nuevo puerto (8005).
    echo.
    pause
