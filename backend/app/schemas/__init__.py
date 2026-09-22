from app.schemas.proveedor import (
    ProveedorBase,
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorResponse,
)
from app.schemas.producto import (
    ProductoBase,
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse,
)
from app.schemas.proveedor_producto import (
    ProveedorProductoBase,
    ProveedorProductoCreate,
    ProveedorProductoUpdate,
    ProveedorProductoResponse,
)
from app.schemas.historial_desempeno import (
    HistorialDesempenoBase,
    HistorialDesempenoCreate,
    HistorialDesempenoResponse,
)
from app.schemas.historial_desempeno_detalle import (
    HistorialDesempenoDetalleBase,
    HistorialDesempenoDetalleCreate,
    HistorialDesempenoDetalleResponse,
)
from app.schemas.evaluacion import (
    EvaluacionBase,
    EvaluacionCreate,
    EvaluacionResponse,
)
from app.schemas.evaluacion_producto import (
    EvaluacionProductoBase,
    EvaluacionProductoCreate,
    EvaluacionProductoResponse,
)
from app.schemas.evaluacion_detalle import (
    EvaluacionDetalleBase,
    EvaluacionDetalleCreate,
    EvaluacionDetalleResponse,
)

__all__ = [
    "ProveedorBase",
    "ProveedorCreate",
    "ProveedorUpdate",
    "ProveedorResponse",
    "ProductoBase",
    "ProductoCreate",
    "ProductoUpdate",
    "ProductoResponse",
    "ProveedorProductoBase",
    "ProveedorProductoCreate",
    "ProveedorProductoUpdate",
    "ProveedorProductoResponse",
    "HistorialDesempenoBase",
    "HistorialDesempenoCreate",
    "HistorialDesempenoResponse",
    "HistorialDesempenoDetalleBase",
    "HistorialDesempenoDetalleCreate",
    "HistorialDesempenoDetalleResponse",
    "EvaluacionBase",
    "EvaluacionCreate",
    "EvaluacionResponse",
    "EvaluacionProductoBase",
    "EvaluacionProductoCreate",
    "EvaluacionProductoResponse",
    "EvaluacionDetalleBase",
    "EvaluacionDetalleCreate",
    "EvaluacionDetalleResponse",
]
