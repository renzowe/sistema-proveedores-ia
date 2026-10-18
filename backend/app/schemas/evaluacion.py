from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.evaluacion_detalle import EvaluacionDetalleResponse
from app.schemas.evaluacion_producto import EvaluacionProductoCreate, EvaluacionProductoResponse

class EvaluacionBase(BaseModel):
    titulo: str
    descripcion_necesidad: Optional[str] = None
    entrega_maxima_dias: Optional[int] = None
    prioridad: Optional[str] = "balanceado"
    estado: Optional[str] = "Pendiente"

class EvaluacionCreate(EvaluacionBase):
    productos: List[EvaluacionProductoCreate]

class EvaluacionResponse(EvaluacionBase):
    id: int
    fecha_evaluacion: Optional[datetime] = None
    productos_solicitados: List[EvaluacionProductoResponse] = []
    detalles_resultado: List[EvaluacionDetalleResponse] = []

    model_config = ConfigDict(from_attributes=True)
