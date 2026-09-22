from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.schemas.producto import ProductoResponse

class HistorialDesempenoDetalleBase(BaseModel):
    producto_id: int
    cantidad_solicitada: int
    cantidad_entregada: int
    porcentaje_defectos: Optional[Decimal] = Decimal("0.0")
    observaciones: Optional[str] = None

class HistorialDesempenoDetalleCreate(HistorialDesempenoDetalleBase):
    pass

class HistorialDesempenoDetalleResponse(HistorialDesempenoDetalleBase):
    id: int
    historial_id: int
    producto: Optional[ProductoResponse] = None

    class Config:
        from_attributes = True
