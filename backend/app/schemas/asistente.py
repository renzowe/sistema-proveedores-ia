from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Topes de tamaño: acotan cuánto texto puede reenviarse a la API de Anthropic
# en cada turno (coste por token) y rechazan payloads abusivos con un 422.
MAX_CARACTERES_MENSAJE = 2000
MAX_MENSAJES_CONVERSACION = 30
MAX_PRODUCTOS_BORRADOR = 50
MAX_CARACTERES_TITULO = 255  # = longitud de la columna evaluaciones.titulo
MAX_CARACTERES_DESCRIPCION = 5000
MAX_CARACTERES_NOMBRE_PRODUCTO = 200
MAX_CARACTERES_ESPECIFICACIONES = 500


class MensajeChatIn(BaseModel):
    rol: Literal["usuario", "asistente"]
    contenido: str = Field(max_length=MAX_CARACTERES_MENSAJE)


class ProductoBorrador(BaseModel):
    nombre_detectado: str = Field(max_length=MAX_CARACTERES_NOMBRE_PRODUCTO)
    cantidad: int = 1
    especificaciones: Optional[str] = Field(default=None, max_length=MAX_CARACTERES_ESPECIFICACIONES)
    producto_id: Optional[int] = None
    producto_nombre_catalogo: Optional[str] = None
    sin_coincidencia: bool = False


class BorradorEvaluacion(BaseModel):
    titulo: Optional[str] = Field(default=None, max_length=MAX_CARACTERES_TITULO)
    descripcion_necesidad: Optional[str] = Field(default=None, max_length=MAX_CARACTERES_DESCRIPCION)
    entrega_maxima_dias: Optional[int] = None
    prioridad: str = "balanceado"
    productos: List[ProductoBorrador] = Field(default_factory=list, max_length=MAX_PRODUCTOS_BORRADOR)


class AsistenteMensajeIn(BaseModel):
    # Transcripción de la conversación; el último mensaje es el que el
    # usuario acaba de enviar. El backend no persiste ninguna conversación:
    # el frontend reenvía los últimos mensajes en cada turno.
    mensajes: List[MensajeChatIn] = Field(max_length=MAX_MENSAJES_CONVERSACION)
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
