from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from src import models, database, auth
from src.config import settings
from src.routers import api, ui, admin
from pathlib import Path
import os

# Create DB Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Sistema de Acompañamiento Integral")

# Configuración de CORS para permitir peticiones desde el frontend/satélites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, usa una lista específica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Session Middleware (Required for Authlib)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY, 
    max_age=3600, 
    https_only=False
)

# Mount Static Files (usando rutas absolutas)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")
ARCHIVOS_DIR = os.path.join(BASE_DIR, "archivos")

# Crear carpetas si no existen
os.makedirs(ARCHIVOS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/archivos", StaticFiles(directory=ARCHIVOS_DIR), name="archivos")

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(api.router)
app.include_router(ui.router)
app.include_router(admin.router)
from src.routers import import_data
app.include_router(import_data.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8005, reload=True)
