from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import (
    proveedores_router,
    productos_router,
    proveedor_productos_router,
    historial_desempeno_router,
    evaluaciones_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API REST para el Sistema Inteligente Agéntico de Evaluación y Selección de Proveedores"
)

# Inicializar tablas en la base de datos al arrancar
@app.on_event("startup")
def on_startup():
    init_db()

# Configuración de CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers bajo /api/v1 como prefijo oficial
app.include_router(proveedores_router, prefix=settings.API_V1_STR)
app.include_router(productos_router, prefix=settings.API_V1_STR)
app.include_router(proveedor_productos_router, prefix=settings.API_V1_STR)
app.include_router(historial_desempeno_router, prefix=settings.API_V1_STR)
app.include_router(evaluaciones_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "sistema": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "estado": "activo",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured",
        "llm_enabled": settings.LLM_ENABLED
    }
