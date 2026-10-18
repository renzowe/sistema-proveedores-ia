from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
