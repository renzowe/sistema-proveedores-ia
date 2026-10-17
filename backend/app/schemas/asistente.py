from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MensajeChatIn(BaseModel):
    rol: Literal["usuario", "asistente"]
    contenido: str


class ProductoBorrador(BaseModel):
    nombre_detectado: str
    cantidad: int = 1
    especificaciones: Optional[str] = None
    producto_id: Optional[int] = None
    producto_nombre_catalogo: Optional[str] = None
    sin_coincidencia: bool = False


class BorradorEvaluacion(BaseModel):
    titulo: Optional[str] = None
    descripcion_necesidad: Optional[str] = None
    entrega_maxima_dias: Optional[int] = None
    prioridad: str = "balanceado"
    productos: List[ProductoBorrador] = []


class AsistenteMensajeIn(BaseModel):
    # Transcripción completa de la conversación hasta ahora; el último
    # mensaje es el que el usuario acaba de enviar. El backend no persiste
    # ninguna conversación: el frontend reenvía el historial en cada turno.
    mensajes: List[MensajeChatIn]
    borrador: BorradorEvaluacion = Field(default_factory=BorradorEvaluacion)
    # Si viene presente, el asistente entra en modo "explicar resultados" de
    # esa evaluación en vez de modo "armar borrador de evaluación nueva".
    evaluacion_id: Optional[int] = None


class AsistenteMensajeOut(BaseModel):
    respuesta: str
    borrador: BorradorEvaluacion
    campos_actualizados: List[str] = []
    listo_para_confirmar: bool = False
    modo: Literal["real", "demostracion"]
    contexto_evaluacion_id: Optional[int] = None
