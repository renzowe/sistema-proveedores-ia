"""
Parser de solicitudes en lenguaje natural hacia la estructura del motor de
evaluación (ver `app.schemas.evaluacion.EvaluacionCreate`).

Este módulo produce la estructura `SolicitudInterpretada` de dos formas
posibles: usando el LLM configurado (Claude, vía Anthropic) cuando está
disponible (`LLM_ENABLED=true` y `ANTHROPIC_API_KEY` configurada), o cayendo
siempre a una extracción heurística local basada en expresiones regulares
cuando el LLM no responde, falla, o está desactivado. El modo heurístico
nunca desaparece: es el piso funcional determinístico del sistema.

Reglas que respeta:
- No inventa productos, cantidades ni prioridades que el texto del usuario no
  mencione explícitamente (el prompt al LLM lo exige explícitamente, y el
  modo heurístico solo puede extraer lo que el regex encuentra).
- No resuelve `producto_id` contra el catálogo real: esa resolución exige
  acceso a la base de datos y es responsabilidad de la capa de servicios,
  no de este parser (mantiene la capa `ai` sin acceso directo a PostgreSQL).
- No depende de que el LLM esté disponible: funciona igual con
  `LLM_ENABLED=false`, y cualquier error del LLM cae automáticamente al
  modo heurístico sin interrumpir al llamador.
"""

import json
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
    interpretado_por: str = "heuristica"  # heuristica | nombre del proveedor LLM (ej. "anthropic")
    confianza: float = 0.0


_PRIORIDADES_VALIDAS = {"precio", "calidad", "logistica", "balanceado"}

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

# Frases de plazo ("entrega en máximo 12 días") se retiran del texto antes de
# extraer productos, para que el regex de productos no confunda "días" (o el
# número de días) con un producto más. `_detectar_plazo` sigue operando sobre
# el texto original, sin este recorte.
_PATRON_PLAZO_CLAUSULA = re.compile(
    r"(?:entrega\s+)?(?:en\s+)?(?:un\s+)?(?:plazo\s+(?:de\s+)?)?(?:m[áa]ximo\s+(?:de\s+)?)?\d+\s*d[ií]as?",
    re.IGNORECASE,
)

_PROMPT_INTERPRETACION = """Eres el módulo de interpretación de solicitudes del Sistema \
Inteligente de Evaluación de Proveedores. Tu única tarea es transformar la solicitud en \
lenguaje natural de un usuario en un JSON estructurado.

REGLA MÁS IMPORTANTE: no inventes productos, cantidades ni plazos que el texto no \
mencione explícitamente. Si el texto no da una cantidad para un producto, usa 1. Si no \
hay prioridad clara, usa "balanceado". Si no hay plazo, usa null.

Responde ÚNICAMENTE con un JSON válido (sin texto adicional, sin markdown, sin \
explicaciones) con esta forma exacta:
{{
  "productos": [
    {{"nombre_detectado": "string", "cantidad": entero, "especificaciones": "string o null"}}
  ],
  "prioridad_sugerida": "precio" | "calidad" | "logistica" | "balanceado",
  "entrega_maxima_dias": entero o null
}}

Texto del usuario:
\"\"\"{texto}\"\"\"
"""


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
    texto_sin_plazo = _PATRON_PLAZO_CLAUSULA.sub(" ", texto)
    productos = []
    for match in _PATRON_PRODUCTO.finditer(texto_sin_plazo):
        cantidad = int(match.group(1))
        nombre = match.group(2).strip(" .,;")
        if nombre:
            productos.append(ProductoInterpretado(nombre_detectado=nombre, cantidad=cantidad))
    return productos


def _interpretacion_heuristica(texto: str) -> SolicitudInterpretada:
    productos = _extraer_productos(texto)
    return SolicitudInterpretada(
        texto_original=texto,
        productos=productos,
        prioridad_sugerida=_detectar_prioridad(texto),
        entrega_maxima_dias=_detectar_plazo(texto),
        interpretado_por="heuristica",
        confianza=0.6 if productos else 0.0,
    )


def _extraer_json(texto_respuesta: str) -> dict:
    """Limpia envoltorios comunes (fences de markdown) antes de parsear JSON."""
    limpio = texto_respuesta.strip()
    if limpio.startswith("```"):
        limpio = re.sub(r"^```(?:json)?", "", limpio).rstrip("`").strip()
    return json.loads(limpio)


def _parsear_respuesta_llm(texto_original: str, contenido: str, proveedor: str) -> Optional[SolicitudInterpretada]:
    """
    Traduce la respuesta JSON del LLM hacia `SolicitudInterpretada`.
    Devuelve None si la respuesta no es un JSON válido o no respeta el
    contrato esperado (nunca propaga la excepción: el llamador cae al modo
    heurístico en ese caso).
    """
    try:
        data = _extraer_json(contenido)

        productos_raw = data.get("productos", [])
        if not isinstance(productos_raw, list):
            return None

        productos = []
        for item in productos_raw:
            nombre = str(item.get("nombre_detectado", "")).strip()
            if not nombre:
                continue
            cantidad = int(item.get("cantidad", 1) or 1)
            especificaciones = item.get("especificaciones") or None
            productos.append(ProductoInterpretado(
                nombre_detectado=nombre,
                cantidad=max(cantidad, 1),
                especificaciones=especificaciones,
            ))

        prioridad = data.get("prioridad_sugerida", "balanceado")
        if prioridad not in _PRIORIDADES_VALIDAS:
            prioridad = "balanceado"

        plazo = data.get("entrega_maxima_dias")
        plazo = int(plazo) if isinstance(plazo, (int, float)) and plazo else None

        return SolicitudInterpretada(
            texto_original=texto_original,
            productos=productos,
            prioridad_sugerida=prioridad,
            entrega_maxima_dias=plazo,
            interpretado_por=proveedor,
            confianza=0.9 if productos else 0.3,
        )
    except (ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError):
        return None


def interpretar_solicitud(texto: str, llm_client: Optional[LLMClient] = None) -> SolicitudInterpretada:
    """
    Transforma una solicitud en lenguaje natural en una `SolicitudInterpretada`.

    Comportamiento:
    - Si se entrega un `llm_client` disponible (`LLM_ENABLED=true` y con API Key
      configurada), se le pide al LLM que devuelva el JSON estructurado. Si
      responde con un JSON válido y coherente, esa es la interpretación usada.
    - En cualquier otro caso (LLM desactivado, sin API Key, error de red/cuota,
      o respuesta no interpretable), se usa la extracción heurística
      determinística basada en expresiones regulares — el piso funcional del
      MVP que no depende de ningún servicio externo.

    Nunca lanza una excepción por ausencia o falla del LLM: siempre devuelve
    una `SolicitudInterpretada` utilizable.
    """
    if llm_client is not None and llm_client.esta_disponible():
        try:
            respuesta = llm_client.generate(
                LLMRequest(
                    prompt=_PROMPT_INTERPRETACION.format(texto=texto),
                    contexto={"tarea": "interpretar_solicitud_evaluacion"},
                    agente="interprete",
                )
            )
            interpretada = _parsear_respuesta_llm(texto, respuesta.contenido, respuesta.proveedor)
            if interpretada is not None:
                return interpretada
        except LLMUnavailableError:
            pass  # Cae al modo heurístico determinístico (comportamiento por defecto del MVP).

    return _interpretacion_heuristica(texto)
