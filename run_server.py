"""
Script de arranque del servidor SAI en producción.
Ejecutado por el servicio Windows a través de NSSM.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

from waitress import serve
from config.wsgi import application

serve(
    application,
    host="0.0.0.0",
    port=8005,
    threads=8,
    channel_timeout=60,
    cleanup_interval=10,
    ident="SAI/Waitress",
)
