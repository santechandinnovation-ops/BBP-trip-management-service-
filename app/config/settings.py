from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    OPENWEATHERMAP_API_KEY: str
    PORT: int = 8002

    class Config:
        case_sensitive = True

def get_settings() -> Settings:
    return Settings(
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
        JWT_EXPIRATION_HOURS=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
        OPENWEATHERMAP_API_KEY=os.getenv("OPENWEATHERMAP_API_KEY", ""),
        PORT=int(os.getenv("PORT", "8002"))
    )

settings = get_settings()
