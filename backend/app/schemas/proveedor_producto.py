from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.schemas.producto import ProductoResponse
from app.schemas.proveedor import ProveedorResponse

class ProveedorProductoBase(BaseModel):
    proveedor_id: int
    producto_id: int
    precio: Decimal
    tiempo_entrega_dias: int
    condiciones: Optional[str] = None
    disponible: Optional[bool] = True

class ProveedorProductoCreate(ProveedorProductoBase):
    pass

class ProveedorProductoUpdate(BaseModel):
    precio: Optional[Decimal] = None
    tiempo_entrega_dias: Optional[int] = None
    condiciones: Optional[str] = None
    disponible: Optional[bool] = None

class ProveedorProductoResponse(ProveedorProductoBase):
    id: int
    fecha_actualizacion: Optional[datetime] = None
    proveedor: Optional[ProveedorResponse] = None
    producto: Optional[ProductoResponse] = None

    class Config:
        from_attributes = True
