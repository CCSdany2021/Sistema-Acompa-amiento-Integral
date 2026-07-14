# manage_service.ps1 - Gestion del Servicio Windows SAI
# Ejecutar como Administrador: .\manage_service.ps1 -Action <accion>
#
# Acciones: install | start | stop | restart | remove | status | logs

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install","start","stop","restart","remove","status","logs")]
    [string]$Action
)

$BASE    = Split-Path -Parent $MyInvocation.MyCommand.Path
$PYTHON  = "$BASE\venv\Scripts\python.exe"
$SCRIPT  = "$BASE\run_server.py"
$SVC     = "SAI_Django"
$LOG_DIR = "$BASE\logs"

function Require-Admin {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "Ejecute este script como Administrador."
        exit 1
    }
}

switch ($Action) {

    "install" {
        Require-Admin
        New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

        Write-Host "Recolectando archivos estaticos..." -ForegroundColor Cyan
        & $PYTHON "$BASE\manage.py" collectstatic --noinput

        Write-Host "Instalando servicio SAI con NSSM..." -ForegroundColor Cyan
        nssm install $SVC $PYTHON $SCRIPT
        nssm set $SVC AppDirectory $BASE
        nssm set $SVC AppStdout    "$LOG_DIR\sai_stdout.log"
        nssm set $SVC AppStderr    "$LOG_DIR\sai_stderr.log"
        nssm set $SVC AppStdoutCreationDisposition 2
        nssm set $SVC AppStderrCreationDisposition 2
        nssm set $SVC DisplayName  "SAI - Sistema de Acompanamiento Integral"
        nssm set $SVC Description  "Servidor Django/Waitress para SAI Calasanz Suba. Puerto 8005."
        nssm set $SVC Start        SERVICE_AUTO_START
        nssm set $SVC AppRestartDelay 5000
        nssm set $SVC AppExit Default Restart

        Write-Host "Servicio SAI instalado y configurado para inicio automatico." -ForegroundColor Green
    }

    "start" {
        Require-Admin
        nssm start $SVC
        Start-Sleep -Seconds 2
        Get-Service -Name $SVC | Select-Object Name, Status, StartType
    }

    "stop" {
        Require-Admin
        nssm stop $SVC
        Write-Host "Servicio SAI detenido." -ForegroundColor Yellow
    }

    "restart" {
        Require-Admin
        nssm restart $SVC
        Start-Sleep -Seconds 3
        Get-Service -Name $SVC | Select-Object Name, Status
    }

    "remove" {
        Require-Admin
        nssm stop $SVC 2>$null
        nssm remove $SVC confirm
        Write-Host "Servicio SAI eliminado." -ForegroundColor Yellow
    }

    "status" {
        try {
            Get-Service -Name $SVC | Select-Object Name, Status, StartType, DisplayName
        } catch {
            Write-Host "El servicio SAI no esta instalado." -ForegroundColor Red
        }
    }

    "logs" {
        $stdout = "$LOG_DIR\sai_stdout.log"
        $stderr = "$LOG_DIR\sai_stderr.log"
        if (Test-Path $stdout) {
            Write-Host "=== STDOUT ===" -ForegroundColor Cyan
            Get-Content $stdout -Tail 50
        }
        if (Test-Path $stderr) {
            $errContent = Get-Content $stderr -Tail 20
            if ($errContent) {
                Write-Host "=== STDERR ===" -ForegroundColor Red
                $errContent
            }
        }
        if (-not (Test-Path $stdout) -and -not (Test-Path $stderr)) {
            Write-Host "No hay logs todavia." -ForegroundColor Yellow
        }
    }
}
