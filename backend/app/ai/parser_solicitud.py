"""
Parser de solicitudes en lenguaje natural hacia la estructura del motor de
evaluación (ver `app.schemas.evaluacion.EvaluacionCreate`).

Fase 11 — preparación arquitectónica:
Este módulo define el CONTRATO (`SolicitudInterpretada`) que tanto un parser
heurístico local como, en la Fase 12, una interpretación real de Claude deben
producir. Mientras la Fase 12 no esté activa, se usa una extracción basada en
expresiones regulares como piso funcional determinístico.

Reglas que respeta:
- No inventa productos, cantidades ni prioridades que el texto del usuario no
  mencione explícitamente.
- No resuelve `producto_id` contra el catálogo real: esa resolución exige
  acceso a la base de datos y es responsabilidad de la capa de servicios,
  no de este parser (mantiene la capa `ai` sin acceso directo a PostgreSQL).
- No depende de que el LLM esté disponible: funciona igual con
  `LLM_ENABLED=false`.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.ai.llm_client import LLMClient, LLMRequest, LLMUnavailableError


@dataclass
class ProductoInterpretado:
    """Un producto detectado dentro del texto libre del usuario."""

    nombre_detectado: str
    cantidad: int
    especificaciones: Optional[str] = None


@dataclass
class SolicitudInterpretada:
    """Estructura resultante de interpretar una solicitud en lenguaje natural."""

    texto_original: str
    productos: List[ProductoInterpretado] = field(default_factory=list)
    prioridad_sugerida: str = "balanceado"
    entrega_maxima_dias: Optional[int] = None
    interpretado_por: str = "heuristica"  # heuristica | claude
    confianza: float = 0.0


_PRIORIDAD_PALABRAS_CLAVE = {
    "precio": ["precio", "económico", "economico", "barato", "menor costo"],
    "calidad": ["calidad", "confiable", "confiabilidad", "garantía", "garantia"],
    "logistica": ["urgente", "rápido", "rapido", "entrega rápida", "entrega rapida", "inmediato"],
}

_PATRON_PRODUCTO = re.compile(
    r"(\d+)\s*(?:unidades?|u\.)?\s*(?:de\s+)?([a-záéíóúñ][a-záéíóúñ\s]*?)(?=(?:,|;|\by\b|\.|$))",
    re.IGNORECASE,
)

_PATRON_PLAZO = re.compile(r"(\d+)\s*d[ií]as?", re.IGNORECASE)


def _detectar_prioridad(texto: str) -> str:
    texto_lower = texto.lower()
    for prioridad, palabras in _PRIORIDAD_PALABRAS_CLAVE.items():
        if any(palabra in texto_lower for palabra in palabras):
            return prioridad
    return "balanceado"


def _detectar_plazo(texto: str) -> Optional[int]:
    match = _PATRON_PLAZO.search(texto)
    return int(match.group(1)) if match else None


def _extraer_productos(texto: str) -> List[ProductoInterpretado]:
    productos = []
    for match in _PATRON_PRODUCTO.finditer(texto):
        cantidad = int(match.group(1))
        nombre = match.group(2).strip(" .,;")
        if nombre:
            productos.append(ProductoInterpretado(nombre_detectado=nombre, cantidad=cantidad))
    return productos


def interpretar_solicitud(texto: str, llm_client: Optional[LLMClient] = None) -> SolicitudInterpretada:
    """
    Transforma una solicitud en lenguaje natural en una `SolicitudInterpretada`.

    Comportamiento:
    - Si se entrega un `llm_client` disponible (`LLM_ENABLED=true` y con API Key
      configurada), se intenta delegar la interpretación a Claude. Como la
      Fase 12 todavía no implementa la llamada real, esto no está operativo
      hoy y el parser cae automáticamente al modo heurístico.
    - En cualquier otro caso (el escenario por defecto del MVP), se usa la
      extracción heurística determinística basada en expresiones regulares.

    Nunca lanza una excepción por ausencia de LLM: siempre devuelve una
    `SolicitudInterpretada` utilizable, aunque sea con confianza baja.
    """
    if llm_client is not None and llm_client.esta_disponible():
        try:
            llm_client.generate(
                LLMRequest(
                    prompt=texto,
                    contexto={"tarea": "interpretar_solicitud_evaluacion"},
                    agente="interprete",
                )
            )
            # La traducción de la respuesta real de Claude hacia
            # `SolicitudInterpretada` se implementará en la Fase 12.
        except (LLMUnavailableError, NotImplementedError):
            pass  # Cae al modo heurístico determinístico (comportamiento por defecto del MVP).

    productos = _extraer_productos(texto)
    return SolicitudInterpretada(
        texto_original=texto,
        productos=productos,
        prioridad_sugerida=_detectar_prioridad(texto),
        entrega_maxima_dias=_detectar_plazo(texto),
        interpretado_por="heuristica",
        confianza=0.6 if productos else 0.0,
    )
