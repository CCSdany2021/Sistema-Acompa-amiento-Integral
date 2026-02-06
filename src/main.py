from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from src import models, database, auth
from src.config import settings
from src.routers import api, ui

# Create DB Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Sistema de Acompañamiento Integral")

# Add Session Middleware (Required for Authlib)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY, 
    max_age=3600, 
    https_only=False
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(api.router)
app.include_router(ui.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
