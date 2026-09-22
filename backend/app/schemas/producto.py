from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    codigo: Optional[str] = None
    estado: Optional[str] = "Activo"

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    codigo: Optional[str] = None
    estado: Optional[str] = None

class ProductoResponse(ProductoBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True
