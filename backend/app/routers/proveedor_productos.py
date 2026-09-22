from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.proveedor_producto import (
    ProveedorProductoCreate,
    ProveedorProductoUpdate,
    ProveedorProductoResponse,
)
from app.services.proveedor_producto_service import ProveedorProductoService

router = APIRouter(prefix="/proveedor-productos", tags=["Proveedor - Productos"])

@router.get("/", response_model=List[ProveedorProductoResponse])
def listar_proveedor_productos(
    proveedor_id: Optional[int] = None,
    producto_id: Optional[int] = None,
    disponible_solo: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return ProveedorProductoService.listar(
        db=db,
        proveedor_id=proveedor_id,
        producto_id=producto_id,
        disponible_solo=disponible_solo,
        skip=skip,
        limit=limit
    )

@router.get("/{id}", response_model=ProveedorProductoResponse)
def obtener_proveedor_producto(id: int, db: Session = Depends(get_db)):
    return ProveedorProductoService.obtener_por_id(db=db, id=id)

@router.post("/", response_model=ProveedorProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor_producto(relacion_in: ProveedorProductoCreate, db: Session = Depends(get_db)):
    return ProveedorProductoService.asignar(db=db, relacion_in=relacion_in)

@router.put("/{id}", response_model=ProveedorProductoResponse)
def actualizar_proveedor_producto(id: int, relacion_in: ProveedorProductoUpdate, db: Session = Depends(get_db)):
    return ProveedorProductoService.actualizar(db=db, id=id, relacion_in=relacion_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proveedor_producto(id: int, db: Session = Depends(get_db)):
    ProveedorProductoService.eliminar(db=db, id=id)
    return None
