"""
Cliente abstracto de comunicación con un modelo de lenguaje (Claude / Anthropic).

Fase 11 — preparación arquitectónica:
Este módulo define el CONTRATO y el punto único de integración que la Fase 12
utilizará para comunicarse realmente con la API de Anthropic. Deliberadamente
NO realiza ninguna llamada de red ni depende del SDK de `anthropic`.

Reglas que este cliente respeta (ver plan de Fase 11):
- No contiene claves API en el código: se leen desde `app.config.settings`.
- No accede directamente a PostgreSQL.
- No modifica resultados de evaluaciones ni datos calculados por el motor
  determinístico: solo produce texto (interpretación/explicación) a partir
  de la información que el llamador le entrega explícitamente.
- Puede desactivarse por completo mediante `LLM_ENABLED=false`.
- La ausencia de API Key nunca impide que el resto del sistema funcione.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.config import settings


class LLMUnavailableError(Exception):
    """
    Se lanza cuando se solicita una generación pero el LLM está desactivado,
    no tiene credenciales configuradas, o (en Fase 12) la comunicación con
    Anthropic falla. El llamador debe capturar esta excepción y continuar
    en modo determinístico: nunca debe interrumpir el flujo principal del MVP.
    """


@dataclass
class LLMRequest:
    """Contrato de entrada para una solicitud al LLM."""

    prompt: str
    contexto: Dict[str, Any] = field(default_factory=dict)
    agente: Optional[str] = None  # financiero | calidad | logistico | riesgo | decisor | interprete


@dataclass
class LLMResponse:
    """Contrato de salida de una respuesta del LLM."""

    contenido: str
    modelo: str
    exitoso: bool
    proveedor: str = "anthropic"
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMClient:
    """
    Interfaz preparada para la futura comunicación con Claude.

    En Fase 11, `generate()` valida disponibilidad y delega en
    `_llamar_anthropic()`, que todavía no está implementado: la
    implementación real (uso del SDK de Anthropic, manejo de reintentos,
    parseo de la respuesta) corresponde a la Fase 12.
    """

    def __init__(self) -> None:
        self.enabled: bool = settings.LLM_ENABLED
        self.api_key: str = settings.ANTHROPIC_API_KEY
        self.model: str = settings.CLAUDE_MODEL
        self.max_tokens: int = settings.CLAUDE_MAX_TOKENS
        self.temperature: float = settings.CLAUDE_TEMPERATURE

    def esta_disponible(self) -> bool:
        """Indica si, en teoría, podría intentarse una llamada real al LLM."""
        return self.enabled and bool(self.api_key)

    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Punto único de entrada para pedir una generación al LLM.

        No debe usarse para decidir puntajes ni resultados de evaluación:
        el motor determinístico (F7) y los agentes (F8) siguen siendo la
        fuente de verdad. Este método solo produce texto complementario
        (interpretación de lenguaje natural o explicaciones).
        """
        if not self.enabled:
            raise LLMUnavailableError("El LLM está desactivado (LLM_ENABLED=false).")
        if not self.api_key:
            raise LLMUnavailableError("No se ha configurado ANTHROPIC_API_KEY.")
        return self._llamar_anthropic(request)

    def _llamar_anthropic(self, request: LLMRequest) -> LLMResponse:
        """
        Implementación real pendiente para la Fase 12.

        Ahí se instanciará el cliente del SDK de Anthropic con `self.api_key`
        y `self.model`, se enviará `request.prompt` junto con `request.contexto`
        y se traducirá la respuesta a un `LLMResponse`.
        """
        raise NotImplementedError(
            "La integración real con la API de Anthropic corresponde a la Fase 12."
        )
