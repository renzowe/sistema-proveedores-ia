import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env file from backend directory if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "Sistema Inteligente Agéntico para Evaluación y Selección de Proveedores"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # El driver (+psycopg2) se deja explícito para que SQLAlchemy no intente
    # autodetectar otro DBAPI (psycopg v3, pg8000, etc.) si psycopg2 llegara
    # a fallar al instalarse/importarse en el entorno de despliegue.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:CHANGE_ME@localhost:5432/sistema-proveedores-ia"
    )
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "127.0.0.1")

    # Orígenes (dominios del frontend) autorizados por CORS, separados por
    # comas. Sin valor, solo se aceptan los servidores locales de desarrollo;
    # en producción debe definirse con la URL pública del frontend.
    CORS_ORIGINS: List[str] = [
        origen.strip()
        for origen in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origen.strip()
    ]

    # Límites de uso del asistente conversacional (protegen el presupuesto de
    # la API de Anthropic frente a abuso: el endpoint es público).
    ASISTENTE_LIMITE_POR_IP: int = int(os.getenv("ASISTENTE_LIMITE_POR_IP", "20"))
    ASISTENTE_VENTANA_SEGUNDOS: int = int(os.getenv("ASISTENTE_VENTANA_SEGUNDOS", "600"))
    ASISTENTE_LIMITE_DIARIO: int = int(os.getenv("ASISTENTE_LIMITE_DIARIO", "200"))

    # Configuración de la capa de IA (Claude, vía API de Anthropic).
    # LLM_ENABLED controla si la capa `app/ai` puede intentar comunicarse con el LLM.
    # Con LLM_ENABLED=false (o sin ANTHROPIC_API_KEY) el sistema sigue
    # funcionando en modo determinístico puro — la arquitectura ya está
    # implementada (no es un stub): solo falta una API Key real para activarla.
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "false").lower() in ("true", "1", "yes")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))

settings = Settings()
