from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.evaluacion_producto import EvaluacionProductoCreate, EvaluacionProductoResponse
from app.schemas.evaluacion_detalle import EvaluacionDetalleResponse

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

    class Config:
        from_attributes = True
