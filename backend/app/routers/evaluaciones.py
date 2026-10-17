from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.asistente import AsistenteMensajeIn, AsistenteMensajeOut
from app.schemas.evaluacion import (
    EvaluacionCreate,
    EvaluacionResponse,
)
from app.services.asistente_service import AsistenteService
from app.services.evaluacion_service import EvaluacionService

router = APIRouter(prefix="/evaluaciones", tags=["Evaluaciones"])


class InterpretarSolicitudIn(BaseModel):
    texto: str


@router.post("/interpretar-solicitud")
def interpretar_solicitud_nl(payload: InterpretarSolicitudIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.interpretar_solicitud_nl(db=db, texto=payload.texto)


@router.get("/asistente/estado")
def obtener_estado_asistente() -> Dict[str, Any]:
    return AsistenteService.estado()


@router.post("/asistente/mensaje", response_model=AsistenteMensajeOut)
def enviar_mensaje_asistente(payload: AsistenteMensajeIn, db: Session = Depends(get_db)):
    return AsistenteService.procesar_mensaje(db=db, payload=payload)


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

@router.post("/{evaluacion_id}/explicacion-ia")
def generar_explicacion_ia(evaluacion_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return EvaluacionService.generar_explicacion_ia(db=db, evaluacion_id=evaluacion_id)

@router.post("/", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
def crear_evaluacion(evaluacion_in: EvaluacionCreate, db: Session = Depends(get_db)):
    return EvaluacionService.crear(db=db, evaluacion_in=evaluacion_in)

@router.delete("/{evaluacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evaluacion(evaluacion_id: int, db: Session = Depends(get_db)):
    EvaluacionService.eliminar(db=db, evaluacion_id=evaluacion_id)
    return None
