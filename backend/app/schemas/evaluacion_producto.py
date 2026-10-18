from typing import Optional

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
