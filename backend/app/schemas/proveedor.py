from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ProveedorBase(BaseModel):
    razon_social: str
    ruc: str
    nombre_comercial: Optional[str] = None
    pais: Optional[str] = "Perú"
    ciudad: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    estado: Optional[str] = "Activo"

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    razon_social: Optional[str] = None
    ruc: Optional[str] = None
    nombre_comercial: Optional[str] = None
    pais: Optional[str] = None
    ciudad: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    estado: Optional[str] = None

class ProveedorResponse(ProveedorBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True
