import hmac
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.asistente import AsistenteMensajeIn, AsistenteMensajeOut
from app.schemas.evaluacion import (
    EvaluacionCreate,
    EvaluacionResponse,
)
from app.services.asistente_service import AsistenteService
from app.services.evaluacion_service import EvaluacionService
from app.utils.limite_uso import LimitadorUso, obtener_ip_cliente

router = APIRouter(prefix="/evaluaciones", tags=["Evaluaciones"])

limitador_asistente = LimitadorUso(
    limite_por_cliente=lambda: settings.ASISTENTE_LIMITE_POR_IP,
    ventana_segundos=lambda: settings.ASISTENTE_VENTANA_SEGUNDOS,
    limite_diario=lambda: settings.ASISTENTE_LIMITE_DIARIO,
)

# Cuenta solo los intentos con un código de acceso incorrecto (anti fuerza bruta).
limitador_codigo = LimitadorUso(
    limite_por_cliente=lambda: settings.ASISTENTE_INTENTOS_CODIGO,
    ventana_segundos=lambda: settings.ASISTENTE_VENTANA_SEGUNDOS,
    limite_diario=lambda: 100_000,
    aviso_por_cliente="Demasiados intentos con un código de acceso incorrecto. Espera {espera} antes de volver a intentarlo.",
)

CABECERA_CODIGO = "X-Codigo-Asistente"


def _acceso_a_claude(request: Request) -> Tuple[bool, Optional[bool]]:
    """
    Devuelve (puede_usar_claude, codigo_valido). Sin ASISTENTE_CODIGO_ACCESO
    configurado no se pide código. Con él, solo el código correcto permite
    usar Claude; si no, el asistente responde en modo demostración.
    """
    codigo_configurado = settings.ASISTENTE_CODIGO_ACCESO
    if not codigo_configurado:
        return True, None

    codigo = request.headers.get(CABECERA_CODIGO, "").strip()
    if not codigo:
        return False, None

    # Se comprueba el límite ANTES de comparar: pasado el límite de intentos
    # fallidos, ni siquiera el código correcto se acepta hasta que expire.
    ip = obtener_ip_cliente(request)
    limitador_codigo.comprobar(ip)
    if hmac.compare_digest(codigo.encode("utf-8"), codigo_configurado.encode("utf-8")):
        return True, True
    limitador_codigo.registrar(ip)
    return False, False


@router.get("/asistente/estado")
def obtener_estado_asistente(request: Request) -> Dict[str, Any]:
    acceso, codigo_valido = _acceso_a_claude(request)
    return AsistenteService.estado(
        permitir_llm=acceso,
        requiere_codigo=bool(settings.ASISTENTE_CODIGO_ACCESO),
        codigo_valido=codigo_valido,
    )


@router.post("/asistente/mensaje", response_model=AsistenteMensajeOut)
def enviar_mensaje_asistente(payload: AsistenteMensajeIn, request: Request, db: Session = Depends(get_db)):
    limitador_asistente.registrar(obtener_ip_cliente(request))
    acceso, _ = _acceso_a_claude(request)
    return AsistenteService.procesar_mensaje(db=db, payload=payload, permitir_llm=acceso)


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
