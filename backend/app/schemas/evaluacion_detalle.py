from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.schemas.proveedor import ProveedorResponse

class EvaluacionDetalleBase(BaseModel):
    proveedor_id: int
    puntaje_precio: Optional[Decimal] = None
    puntaje_calidad: Optional[Decimal] = None
    puntaje_logistica: Optional[Decimal] = None
    puntaje_historial: Optional[Decimal] = None
    puntaje_riesgo: Optional[Decimal] = None
    puntaje_final: Optional[Decimal] = None
    recomendado: Optional[bool] = False
    explicacion: Optional[str] = None

class EvaluacionDetalleCreate(EvaluacionDetalleBase):
    pass

class EvaluacionDetalleResponse(EvaluacionDetalleBase):
    id: int
    evaluacion_id: int
    fecha_calculo: Optional[datetime] = None
    proveedor: Optional[ProveedorResponse] = None

    class Config:
        from_attributes = True
