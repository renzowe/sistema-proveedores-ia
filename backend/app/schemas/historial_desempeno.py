from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from app.schemas.proveedor import ProveedorResponse
from app.schemas.historial_desempeno_detalle import (
    HistorialDesempenoDetalleCreate,
    HistorialDesempenoDetalleResponse
)

class HistorialDesempenoBase(BaseModel):
    proveedor_id: int
    fecha_operacion: date
    tiempo_entrega_promedio_dias: Optional[int] = None
    cumplimiento_porcentaje: Optional[Decimal] = None
    observaciones: Optional[str] = None

class HistorialDesempenoCreate(HistorialDesempenoBase):
    detalles: Optional[List[HistorialDesempenoDetalleCreate]] = []

class HistorialDesempenoResponse(HistorialDesempenoBase):
    id: int
    fecha_registro: Optional[datetime] = None
    proveedor: Optional[ProveedorResponse] = None
    detalles: List[HistorialDesempenoDetalleResponse] = []

    class Config:
        from_attributes = True
