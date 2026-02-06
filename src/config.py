import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Acompañamiento Integral"
    DATABASE_URL: str = "postgresql://postgres:password@localhost/acompanamiento_db"
    SECRET_KEY: str = "your-secret-key-here"
    
    # Microsoft 365 Config
    MS_CLIENT_ID: str = ""
    MS_CLIENT_SECRET: str = ""
    MS_TENANT_ID: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
