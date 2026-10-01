import os
from pathlib import Path
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
    
    # Configuración de la capa de IA (Fase 11: preparación arquitectónica).
    # LLM_ENABLED controla si la capa `app/ai` puede intentar comunicarse con Claude.
    # Por defecto permanece desactivada y el sistema funciona en modo determinístico puro.
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "false").lower() in ("true", "1", "yes")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
    CLAUDE_TEMPERATURE: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.2"))

settings = Settings()
