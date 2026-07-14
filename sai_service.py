"""
Servicio Windows para SAI (Sistema de Acompañamiento Integral)
Usa Waitress como servidor WSGI de producción.

Instalar:   python sai_service.py install
Iniciar:    python sai_service.py start
Detener:    python sai_service.py stop
Eliminar:   python sai_service.py remove
"""

import sys
import os
import threading
import logging

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_SITE_PACKAGES = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")

# Agregar venv al path si no está
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

import win32serviceutil
import win32service
import win32event
import servicemanager

# Configurar Django antes de importar waitress
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, BASE_DIR)

LOG_FILE = os.path.join(BASE_DIR, "logs", "sai_service.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SAIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SAI_Django"
    _svc_display_name_ = "SAI - Sistema de Acompañamiento Integral"
    _svc_description_ = (
        "Servidor web Django para el Sistema de Acompañamiento Integral "
        "del Colegio Calasanz Suba. Puerto 8005."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._server = None
        self._thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logging.info("Deteniendo servicio SAI...")
        if self._server:
            self._server.close()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        logging.info("Iniciando servicio SAI en puerto 8005...")

        try:
            os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

            from waitress import create_server
            from config.wsgi import application

            self._server = create_server(
                application,
                host="0.0.0.0",
                port=8005,
                threads=8,
                channel_timeout=60,
                cleanup_interval=10,
            )
            logging.info("Servidor Waitress iniciado en 0.0.0.0:8005")

            self._thread = threading.Thread(target=self._server.run, daemon=True)
            self._thread.start()

            # Esperar señal de parada
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        except Exception as exc:
            logging.exception("Error fatal en el servicio SAI: %s", exc)
            servicemanager.LogErrorMsg(f"SAI Service Error: {exc}")

        logging.info("Servicio SAI detenido.")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SAIService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SAIService)
