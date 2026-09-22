from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.schemas.historial_desempeno import (
    HistorialDesempenoCreate,
    HistorialDesempenoResponse,
)
from app.services.historial_service import HistorialService

router = APIRouter(prefix="/historial-desempeno", tags=["Historial de Desempeño"])

@router.get("/", response_model=List[HistorialDesempenoResponse])
def listar_historial(
    proveedor_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return HistorialService.listar(db=db, proveedor_id=proveedor_id, skip=skip, limit=limit)

@router.get("/{id}", response_model=HistorialDesempenoResponse)
def obtener_historial(id: int, db: Session = Depends(get_db)):
    return HistorialService.obtener_por_id(db=db, id=id)

@router.get("/proveedor/{proveedor_id}/metricas")
def obtener_metricas_proveedor(proveedor_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return HistorialService.obtener_metricas_proveedor(db=db, proveedor_id=proveedor_id)

@router.get("/producto/{producto_id}")
def obtener_historial_por_producto(
    producto_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    return HistorialService.obtener_historial_por_producto(
        db=db, producto_id=producto_id, skip=skip, limit=limit
    )

@router.post("/", response_model=HistorialDesempenoResponse, status_code=status.HTTP_201_CREATED)
def registrar_historial(historial_in: HistorialDesempenoCreate, db: Session = Depends(get_db)):
    return HistorialService.registrar(db=db, historial_in=historial_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_historial(id: int, db: Session = Depends(get_db)):
    HistorialService.eliminar(db=db, id=id)
    return None
