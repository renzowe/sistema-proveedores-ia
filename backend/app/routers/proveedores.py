from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate, ProveedorResponse
from app.services.proveedor_service import ProveedorService

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])

@router.get("/", response_model=List[ProveedorResponse])
def listar_proveedores(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return ProveedorService.listar(db=db, skip=skip, limit=limit, estado=estado)

@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    return ProveedorService.obtener_por_id(db=db, proveedor_id=proveedor_id)

@router.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor(proveedor_in: ProveedorCreate, db: Session = Depends(get_db)):
    return ProveedorService.crear(db=db, proveedor_in=proveedor_in)

@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def actualizar_proveedor(proveedor_id: int, proveedor_in: ProveedorUpdate, db: Session = Depends(get_db)):
    return ProveedorService.actualizar(db=db, proveedor_id=proveedor_id, proveedor_in=proveedor_in)

@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    ProveedorService.eliminar(db=db, proveedor_id=proveedor_id)
    return None
