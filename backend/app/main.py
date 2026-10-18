import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.llm_client import LLMClient
from app.config import settings
from app.database import init_db
from app.routers import (
    proveedores_router,
    productos_router,
    proveedor_productos_router,
    historial_desempeno_router,
    evaluaciones_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas que falten al arrancar.
    init_db()
    if LLMClient().esta_disponible() and not settings.ASISTENTE_CODIGO_ACCESO:
        logging.getLogger("uvicorn.error").warning(
            "El asistente usa Claude real SIN código de acceso: cualquiera con el enlace "
            "puede consumir la API Key. En producción define ASISTENTE_CODIGO_ACCESO."
        )
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API REST para el Sistema Inteligente Agéntico de Evaluación y Selección de Proveedores",
    lifespan=lifespan,
)

# Solo los orígenes de CORS_ORIGINS pueden llamar a la API desde un navegador.
# La aplicación no usa cookies ni sesiones, así que no se permiten credenciales.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Codigo-Asistente"],
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
        "llm_enabled": settings.LLM_ENABLED
    }
