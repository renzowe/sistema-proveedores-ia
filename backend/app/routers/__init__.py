from app.routers.proveedores import router as proveedores_router
from app.routers.productos import router as productos_router
from app.routers.proveedor_productos import router as proveedor_productos_router
from app.routers.historial_desempeno import router as historial_desempeno_router
from app.routers.evaluaciones import router as evaluaciones_router

__all__ = [
    "proveedores_router",
    "productos_router",
    "proveedor_productos_router",
    "historial_desempeno_router",
    "evaluaciones_router",
]
