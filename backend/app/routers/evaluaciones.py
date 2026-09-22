from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.schemas.evaluacion import (
    EvaluacionCreate,
    EvaluacionResponse,
)
from app.services.evaluacion_service import EvaluacionService

router = APIRouter(prefix="/evaluaciones", tags=["Evaluaciones"])

@router.get("/", response_model=List[EvaluacionResponse])
def listar_evaluaciones(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return EvaluacionService.listar(db=db, skip=skip, limit=limit, estado=estado)

@router.get("/{evaluacion_id}", response_model=EvaluacionResponse)
def obtener_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)):
    return EvaluacionService.obtener_por_id(db=db, evaluacion_id=evaluacion_id)

@router.get("/{evaluacion_id}/proveedores-compatibles")
def buscar_proveedores_compatibles(evaluacion_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.buscar_proveedores_compatibles(db=db, evaluacion_id=evaluacion_id)

@router.post("/{evaluacion_id}/procesar")
def procesar_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.ejecutar_evaluacion(db=db, evaluacion_id=evaluacion_id)

@router.get("/{evaluacion_id}/resultados")
def obtener_resultados_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.obtener_resultados(db=db, evaluacion_id=evaluacion_id)

@router.get("/{evaluacion_id}/informe-agentes")
def obtener_informe_agentes(evaluacion_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.obtener_informe_agentes(db=db, evaluacion_id=evaluacion_id)

@router.post("/", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
def crear_evaluacion(evaluacion_in: EvaluacionCreate, db: Session = Depends(get_db)):
    return EvaluacionService.crear(db=db, evaluacion_in=evaluacion_in)

@router.delete("/{evaluacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)):
    EvaluacionService.eliminar(db=db, evaluacion_id=evaluacion_id)
    return None
