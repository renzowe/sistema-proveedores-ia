from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.proveedor_producto import ProveedorProducto
from app.models.historial_desempeno import HistorialDesempeno
from app.models.historial_desempeno_detalle import HistorialDesempenoDetalle
from app.models.evaluacion import Evaluacion
from app.models.evaluacion_producto import EvaluacionProducto
from app.models.evaluacion_detalle import EvaluacionDetalle

__all__ = [
    "Proveedor",
    "Producto",
    "ProveedorProducto",
    "HistorialDesempeno",
    "HistorialDesempenoDetalle",
    "Evaluacion",
    "EvaluacionProducto",
    "EvaluacionDetalle",
]
