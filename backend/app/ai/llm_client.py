"""
Cliente de comunicación con el modelo de lenguaje (Claude, vía API de Anthropic).

Implementación real (no un stub): usa el SDK oficial `anthropic`. Lo único
que falta para que funcione en producción es una `ANTHROPIC_API_KEY` válida
en `backend/.env` (y en las variables de entorno de Render) — no hace falta
tocar este archivo.

Reglas que este cliente respeta:
- No contiene claves API en el código: se leen desde `app.config.settings`.
- No accede directamente a PostgreSQL.
- No modifica resultados de evaluaciones ni datos calculados por el motor
  determinístico: solo produce texto (interpretación/explicación) a partir
  de la información que el llamador le entrega explícitamente.
- Puede desactivarse por completo mediante `LLM_ENABLED=false`.
- La ausencia de API Key, o cualquier error de red/cuota/autenticación,
  nunca impide que el resto del sistema funcione: se traduce siempre a
  `LLMUnavailableError` para que el llamador pueda caer al modo
  determinístico sin interrumpir el flujo principal del MVP.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import anthropic

from app.config import settings


class LLMUnavailableError(Exception):
    """
    Se lanza cuando se solicita una generación pero el LLM está desactivado,
    no tiene credenciales configuradas, o la comunicación con Claude falla
    (red, cuota, autenticación, modelo no disponible, etc.). El llamador
    debe capturar esta excepción y continuar en modo determinístico: nunca
    debe interrumpir el flujo principal del MVP.
    """


@dataclass
class LLMRequest:
    """Contrato de entrada para una solicitud al LLM."""

    prompt: str
    contexto: Dict[str, Any] = field(default_factory=dict)
    agente: Optional[str] = None  # financiero | calidad | logistico | riesgo | decisor | interprete
    system: Optional[str] = None
    historial: List[Dict[str, str]] = field(default_factory=list)  # [{"role": "user"|"assistant", "content": "..."}]


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
    Cliente para la comunicación real con Claude (API de Anthropic).

    `generate()` valida disponibilidad y delega en `_llamar_claude()`, que
    usa el SDK `anthropic`. El motor determinístico (F7) y los agentes
    basados en reglas (F8) siguen siendo la única fuente de puntajes y
    recomendaciones: este cliente solo produce texto complementario.
    """

    def __init__(self) -> None:
        self.enabled: bool = settings.LLM_ENABLED
        self.api_key: str = settings.ANTHROPIC_API_KEY
        self.model: str = settings.CLAUDE_MODEL
        self.max_tokens: int = settings.CLAUDE_MAX_TOKENS

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
        return self._llamar_claude(request)

    def _llamar_claude(self, request: LLMRequest) -> LLMResponse:
        """
        Llamada real a la API de Anthropic usando el SDK `anthropic`.

        Se fija un timeout y un número de reintentos acotado (lección
        aprendida probando este mismo cliente contra Gemini: sin esto, una
        sobrecarga transitoria del proveedor puede dejar la solicitud
        colgada varios minutos por el backoff por defecto del SDK,
        bloqueando tanto los tests como el endpoint real que lo use).
        """
        try:
            client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=20.0,
                max_retries=1,
            )
            mensajes = [*request.historial, {"role": "user", "content": request.prompt}]
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": mensajes,
            }
            if request.system:
                kwargs["system"] = request.system
            response = client.messages.create(**kwargs)
        except anthropic.AnthropicError as exc:
            mensaje = getattr(exc, "message", None) or str(exc)
            raise LLMUnavailableError(f"Claude no pudo procesar la solicitud: {mensaje}") from exc
        except Exception as exc:  # errores de red, timeouts, etc.
            raise LLMUnavailableError(f"No se pudo contactar a Claude: {exc}") from exc

        bloques_texto = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        texto = "".join(bloques_texto).strip()
        if not texto:
            raise LLMUnavailableError("Claude respondió sin contenido de texto utilizable.")

        metadata = {"agente": request.agente}
        if getattr(response, "usage", None) is not None:
            metadata["input_tokens"] = response.usage.input_tokens
            metadata["output_tokens"] = response.usage.output_tokens

        return LLMResponse(
            contenido=texto,
            modelo=self.model,
            exitoso=True,
            proveedor="anthropic",
            metadata=metadata,
        )
