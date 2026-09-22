from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from app.services.producto_service import ProductoService

router = APIRouter(prefix="/productos", tags=["Productos"])

@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return ProductoService.listar(db=db, skip=skip, limit=limit, estado=estado)

@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    return ProductoService.obtener_por_id(db=db, producto_id=producto_id)

@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(producto_in: ProductoCreate, db: Session = Depends(get_db)):
    return ProductoService.crear(db=db, producto_in=producto_in)

@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(producto_id: int, producto_in: ProductoUpdate, db: Session = Depends(get_db)):
    return ProductoService.actualizar(db=db, producto_id=producto_id, producto_in=producto_in)

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    ProductoService.eliminar(db=db, producto_id=producto_id)
    return None
