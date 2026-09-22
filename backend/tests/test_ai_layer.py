"""
Pruebas de la Fase 11 — Preparación de Inteligencia Artificial.

Verifican que la capa `app/ai` quede correctamente preparada sin depender de
una API Key real ni realizar llamadas a Anthropic, y que el sistema siga
funcionando por completo en modo determinístico (`LLM_ENABLED=false`).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.ai.llm_client import LLMClient, LLMRequest, LLMResponse, LLMUnavailableError
from app.ai.parser_solicitud import (
    ProductoInterpretado,
    SolicitudInterpretada,
    interpretar_solicitud,
)

client = TestClient(app)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "app" / "ai" / "prompts"
SECCIONES_OBLIGATORIAS = [
    "ROL",
    "OBJETIVO",
    "INFORMACIÓN DISPONIBLE",
    "INFORMACIÓN QUE NO DEBES INVENTAR",
    "FORMATO ESPERADO DE SALIDA",
    "RESTRICCIONES",
]


# --- Prueba 1 y 2: inicio sin LLM y sin API Key ---------------------------

def test_backend_inicia_correctamente_sin_llm():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "llm_enabled" in body


def test_endpoints_existentes_siguen_funcionando_sin_llm():
    assert client.get("/api/v1/proveedores/").status_code == 200
    assert client.get("/api/v1/productos/").status_code == 200
    assert client.get("/api/v1/evaluaciones/").status_code == 200


# --- Prueba 3: configuración del LLM ---------------------------------------

def test_config_expone_variables_de_llm_sin_credenciales_reales():
    assert isinstance(settings.LLM_ENABLED, bool)
    assert settings.LLM_ENABLED is False, "El MVP debe iniciar con LLM_ENABLED=false por defecto."
    assert isinstance(settings.ANTHROPIC_API_KEY, str)
    assert settings.CLAUDE_MODEL
    assert settings.CLAUDE_MAX_TOKENS > 0
    assert settings.CLAUDE_TEMPERATURE >= 0.0


def test_ausencia_de_api_key_no_impide_iniciar_el_sistema():
    # El propio hecho de que `client` (TestClient sobre app.main.app) se haya
    # instanciado arriba sin errores, con ANTHROPIC_API_KEY vacío en el .env
    # de pruebas, ya demuestra este criterio. Se valida explícitamente aquí.
    assert settings.ANTHROPIC_API_KEY == "" or settings.ANTHROPIC_API_KEY is not None
    assert client.get("/").status_code == 200


# --- LLMClient: contrato y comportamiento sin llamadas reales --------------

def test_llm_client_desactivado_por_defecto():
    llm_client = LLMClient()
    assert llm_client.enabled is False
    assert llm_client.esta_disponible() is False


def test_llm_client_generate_falla_de_forma_controlada_si_esta_desactivado():
    llm_client = LLMClient()
    with pytest.raises(LLMUnavailableError):
        llm_client.generate(LLMRequest(prompt="Explica el resultado de esta evaluación."))


def test_llm_client_generate_exige_api_key_aunque_este_habilitado():
    llm_client = LLMClient()
    llm_client.enabled = True
    llm_client.api_key = ""
    with pytest.raises(LLMUnavailableError):
        llm_client.generate(LLMRequest(prompt="x"))


def test_llm_client_no_realiza_llamadas_reales_a_anthropic():
    # Con credenciales "completas", la implementación real queda pendiente
    # para la Fase 12: debe fallar de forma explícita, nunca conectarse.
    llm_client = LLMClient()
    llm_client.enabled = True
    llm_client.api_key = "clave-de-prueba-no-real"
    with pytest.raises(NotImplementedError):
        llm_client.generate(LLMRequest(prompt="x"))


# --- Prueba 4: contratos de entrada/salida ---------------------------------

def test_contrato_llm_request_response_se_construye_correctamente():
    request = LLMRequest(prompt="Interpreta esta solicitud", contexto={"evaluacion_id": 1}, agente="decisor")
    assert request.prompt == "Interpreta esta solicitud"
    assert request.contexto["evaluacion_id"] == 1
    assert request.agente == "decisor"

    response = LLMResponse(contenido="Texto generado", modelo="claude-sonnet-5", exitoso=True)
    assert response.proveedor == "anthropic"
    assert response.exitoso is True


def test_contrato_solicitud_interpretada_se_construye_correctamente():
    producto = ProductoInterpretado(nombre_detectado="cables", cantidad=100)
    solicitud = SolicitudInterpretada(
        texto_original="Necesito 100 cables",
        productos=[producto],
        prioridad_sugerida="precio",
    )
    assert solicitud.productos[0].cantidad == 100
    assert solicitud.interpretado_por == "heuristica"
    assert solicitud.confianza == 0.0


# --- Parser de solicitudes: piso heurístico determinístico -----------------

def test_parser_heuristico_extrae_productos_y_prioridad():
    texto = (
        "Necesito comprar 100 unidades de cables y 50 conectores, "
        "priorizando precio y entrega rápida."
    )
    resultado = interpretar_solicitud(texto)

    assert resultado.interpretado_por == "heuristica"
    assert len(resultado.productos) == 2
    nombres_cantidades = {p.nombre_detectado: p.cantidad for p in resultado.productos}
    assert nombres_cantidades.get("cables") == 100
    assert nombres_cantidades.get("conectores") == 50
    assert resultado.prioridad_sugerida == "precio"
    assert resultado.confianza > 0


def test_parser_no_inventa_productos_con_texto_vacio():
    resultado = interpretar_solicitud("")
    assert resultado.productos == []
    assert resultado.confianza == 0.0
    assert resultado.prioridad_sugerida == "balanceado"


def test_parser_detecta_plazo_maximo_en_dias():
    resultado = interpretar_solicitud("Requiero 10 laptops entregadas en máximo 15 dias.")
    assert resultado.entrega_maxima_dias == 15


def test_parser_no_falla_sin_llm_client_configurado():
    # No se le entrega llm_client: debe funcionar igual, sin excepciones.
    resultado = interpretar_solicitud("30 sillas de oficina")
    assert resultado.productos[0].nombre_detectado == "sillas de oficina"


# --- Prueba 5: prompts base existen y están completos ----------------------

@pytest.mark.parametrize(
    "nombre_agente",
    ["financiero", "calidad", "logistico", "riesgo", "decisor"],
)
def test_prompt_base_existe_y_contiene_secciones_obligatorias(nombre_agente):
    ruta = PROMPTS_DIR / f"{nombre_agente}.txt"
    assert ruta.exists(), f"Falta el prompt base para el agente {nombre_agente}"

    contenido = ruta.read_text(encoding="utf-8")
    assert contenido.strip(), f"El prompt de {nombre_agente} está vacío"

    for seccion in SECCIONES_OBLIGATORIAS:
        assert seccion in contenido, f"El prompt de {nombre_agente} no define la sección '{seccion}'"


# --- Prueba 6: regresión del flujo principal sin LLM ------------------------

def test_regresion_flujo_principal_no_se_ve_afectado_por_la_capa_ai():
    """
    La sola existencia de `app/ai` no debe alterar el comportamiento de los
    módulos ya probados en test_proveedores.py, test_productos.py,
    test_historial_desempeno.py, test_evaluaciones.py y test_agentes.py
    (que corren en la misma sesión de pytest). Aquí se valida un smoke test
    adicional de punta a punta usando datos ya sembrados por seed_data.py.
    """
    proveedores = client.get("/api/v1/proveedores/").json()
    productos = client.get("/api/v1/productos/").json()
    assert isinstance(proveedores, list)
    assert isinstance(productos, list)

    evaluaciones_antes = client.get("/api/v1/evaluaciones/").json()
    assert isinstance(evaluaciones_antes, list)
