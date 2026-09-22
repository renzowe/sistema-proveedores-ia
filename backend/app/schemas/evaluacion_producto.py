from pydantic import BaseModel
from typing import Optional
from app.schemas.producto import ProductoResponse

class EvaluacionProductoBase(BaseModel):
    producto_id: int
    cantidad: int
    especificaciones: Optional[str] = None

class EvaluacionProductoCreate(EvaluacionProductoBase):
    pass

class EvaluacionProductoResponse(EvaluacionProductoBase):
    id: int
    evaluacion_id: int
    producto: Optional[ProductoResponse] = None

    class Config:
        from_attributes = True
