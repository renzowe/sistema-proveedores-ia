from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

if not settings.DATABASE_URL:
    raise RuntimeError(
        "Falta DATABASE_URL: defínela en backend/.env (ver backend/.env.example), "
        "en docker-compose o en las variables de entorno del servidor."
    )

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import app.models  # Asegura que todos los modelos estén cargados
    Base.metadata.create_all(bind=engine)
