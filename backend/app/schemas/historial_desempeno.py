from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.historial_desempeno_detalle import (
    HistorialDesempenoDetalleCreate,
    HistorialDesempenoDetalleResponse
)
from app.schemas.proveedor import ProveedorResponse

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

    model_config = ConfigDict(from_attributes=True)
