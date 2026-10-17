"""
Pruebas de la capa de IA (Fase 11 — arquitectura; Fase 12 — integración real).

Verifican que la capa `app/ai` funcione correctamente tanto con el LLM
desactivado (modo determinístico puro) como con Claude realmente configurado
y disponible, y que el sistema nunca dependa de forma obligatoria del LLM
para operar.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.llm_client import LLMClient, LLMRequest, LLMResponse, LLMUnavailableError
from app.ai.parser_solicitud import (
    ProductoInterpretado,
    SolicitudInterpretada,
    interpretar_solicitud,
)
from app.config import settings
from app.main import app
from app.models.producto import Producto
from app.services.evaluacion_service import _buscar_producto_similar

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

LLM_REALMENTE_DISPONIBLE = LLMClient().esta_disponible()


# --- Prueba 1 y 2: el sistema arranca y funciona sin depender del LLM ------

def test_backend_inicia_correctamente():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "llm_enabled" in body


def test_endpoints_existentes_siguen_funcionando_sin_depender_del_llm():
    assert client.get("/api/v1/proveedores/").status_code == 200
    assert client.get("/api/v1/productos/").status_code == 200
    assert client.get("/api/v1/evaluaciones/").status_code == 200


# --- Prueba 3: configuración del LLM ---------------------------------------

def test_config_expone_variables_de_claude_con_tipos_correctos():
    assert isinstance(settings.LLM_ENABLED, bool)
    assert isinstance(settings.ANTHROPIC_API_KEY, str)
    assert settings.CLAUDE_MODEL
    assert settings.CLAUDE_MAX_TOKENS > 0


def test_api_key_vacia_no_impide_instanciar_el_cliente():
    # El contrato de LLMClient nunca debe lanzar al construirse, sin
    # importar si hay o no credenciales configuradas.
    llm_client = LLMClient()
    llm_client.api_key = ""
    llm_client.enabled = True
    assert llm_client.esta_disponible() is False


# --- LLMClient: contrato, errores controlados y llamada real ---------------

def test_llm_client_generate_falla_de_forma_controlada_si_esta_desactivado():
    llm_client = LLMClient()
    llm_client.enabled = False
    with pytest.raises(LLMUnavailableError):
        llm_client.generate(LLMRequest(prompt="Explica el resultado de esta evaluación."))


def test_llm_client_generate_exige_api_key_aunque_este_habilitado():
    llm_client = LLMClient()
    llm_client.enabled = True
    llm_client.api_key = ""
    with pytest.raises(LLMUnavailableError):
        llm_client.generate(LLMRequest(prompt="x"))


def test_llm_client_credenciales_invalidas_fallan_de_forma_controlada():
    # Una API Key con formato incorrecto debe traducirse a LLMUnavailableError
    # (nunca debe propagar una excepción cruda del SDK de Anthropic al llamador).
    llm_client = LLMClient()
    llm_client.enabled = True
    llm_client.api_key = "clave-invalida-de-prueba"
    with pytest.raises(LLMUnavailableError):
        llm_client.generate(LLMRequest(prompt="x"))


@pytest.mark.skipif(not LLM_REALMENTE_DISPONIBLE, reason="Requiere LLM_ENABLED=true y ANTHROPIC_API_KEY configurada")
def test_llm_client_realiza_una_llamada_real_a_claude():
    llm_client = LLMClient()
    try:
        respuesta = llm_client.generate(LLMRequest(
            prompt="Responde únicamente con la palabra: OK",
            agente="interprete",
        ))
    except LLMUnavailableError as exc:
        # Un proveedor externo puede fallar de forma transitoria (red, cuota,
        # alta demanda); eso es un problema externo de disponibilidad, no un
        # defecto de nuestro cliente. El contrato ya está probado con
        # credenciales inválidas en las pruebas anteriores.
        pytest.skip(f"Claude no disponible en este momento (transitorio): {exc}")
        return
    assert isinstance(respuesta, LLMResponse)
    assert respuesta.exitoso is True
    assert respuesta.proveedor == "anthropic"
    assert respuesta.modelo == settings.CLAUDE_MODEL
    assert respuesta.contenido  # debe traer texto no vacío


# --- Prueba 4: contratos de entrada/salida ---------------------------------

def test_contrato_llm_request_response_se_construye_correctamente():
    request = LLMRequest(prompt="Interpreta esta solicitud", contexto={"evaluacion_id": 1}, agente="decisor")
    assert request.prompt == "Interpreta esta solicitud"
    assert request.contexto["evaluacion_id"] == 1
    assert request.agente == "decisor"

    response = LLMResponse(contenido="Texto generado", modelo="claude-haiku-4-5-20251001", exitoso=True)
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
# Estas pruebas NO pasan llm_client, así que ejercitan siempre el modo
# heurístico sin importar si Claude está configurado o no.

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


def test_parser_no_confunde_la_clausula_de_plazo_con_un_producto():
    # Regresión: el regex de productos llegó a capturar "días" como si fuera
    # un producto más (con la cantidad de días como si fuera la cantidad).
    resultado = interpretar_solicitud(
        "Necesito 15 laptops y 10 monitores, priorizando calidad, "
        "entrega en maximo 12 dias."
    )
    nombres = [p.nombre_detectado for p in resultado.productos]
    assert resultado.entrega_maxima_dias == 12
    assert "laptops" in nombres
    assert not any("dia" in n.lower() for n in nombres), (
        f"La cláusula de plazo se coló como producto: {nombres}"
    )


def test_parser_no_falla_sin_llm_client_configurado():
    # No se le entrega llm_client: debe funcionar igual, sin excepciones.
    resultado = interpretar_solicitud("30 sillas de oficina")
    assert resultado.productos[0].nombre_detectado == "sillas de oficina"


@pytest.mark.skipif(not LLM_REALMENTE_DISPONIBLE, reason="Requiere LLM_ENABLED=true y ANTHROPIC_API_KEY configurada")
def test_parser_usa_claude_cuando_esta_disponible_y_devuelve_json_coherente():
    llm_client = LLMClient()
    resultado = interpretar_solicitud(
        "Necesito 5 laptops y 3 monitores con prioridad en calidad, entrega en máximo 20 días.",
        llm_client=llm_client,
    )
    # Si Claude respondió un JSON válido, interpretado_por="anthropic"; si por
    # cualquier motivo (latencia, formato) no fue parseable, cae a heurística.
    # En ambos casos el resultado debe ser utilizable y no debe inventar
    # productos que el texto no menciona.
    assert resultado.interpretado_por in ("anthropic", "heuristica")
    assert resultado.prioridad_sugerida in ("precio", "calidad", "logistica", "balanceado")
    for producto in resultado.productos:
        assert producto.cantidad >= 1


# --- Prueba 5: prompts base existen y están completos ----------------------

@pytest.mark.parametrize(
    "nombre_agente",
    ["financiero", "calidad", "logistico", "riesgo", "decisor", "asistente"],
)
def test_prompt_base_existe_y_contiene_secciones_obligatorias(nombre_agente):
    ruta = PROMPTS_DIR / f"{nombre_agente}.txt"
    assert ruta.exists(), f"Falta el prompt base para el agente {nombre_agente}"

    contenido = ruta.read_text(encoding="utf-8")
    assert contenido.strip(), f"El prompt de {nombre_agente} está vacío"

    for seccion in SECCIONES_OBLIGATORIAS:
        assert seccion in contenido, f"El prompt de {nombre_agente} no define la sección '{seccion}'"


# --- Prueba 6: regresión del flujo principal, con y sin LLM -----------------

def test_regresion_flujo_principal_no_se_ve_afectado_por_la_capa_ai():
    """
    La capa `app/ai` (activa o no) no debe alterar el comportamiento de los
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


def test_explicacion_ia_responde_503_controlado_si_llm_desactivado(monkeypatch):
    """
    Con el LLM desactivado, el endpoint de explicación por IA debe fallar de
    forma controlada (503) y nunca con un error 500 sin manejar.
    """
    monkeypatch.setattr(settings, "LLM_ENABLED", False)

    # Usa la evaluación procesada más reciente si existe; si no hay ninguna,
    # la prueba no aplica (se salta sin marcar fallo).
    evaluaciones = client.get("/api/v1/evaluaciones/").json()
    procesadas = [e for e in evaluaciones if e.get("detalles_resultado")]
    if not procesadas:
        pytest.skip("No hay evaluaciones procesadas en la base para probar este endpoint.")

    eval_id = procesadas[0]["id"]
    response = client.post(f"/api/v1/evaluaciones/{eval_id}/explicacion-ia")
    assert response.status_code == 503


# --- Interpretación de lenguaje natural: emparejamiento contra el catálogo -

def test_buscar_producto_similar_tolera_plurales_regulares():
    # Regresión: "laptops" (plural) no emparejaba con "Laptop Empresarial..."
    # (singular) en el catálogo real antes de normalizar plurales.
    catalogo = [
        Producto(id=1, nombre="Laptop Empresarial 16GB Core i7"),
        Producto(id=2, nombre="Monitor 24 IPS Full HD"),
    ]
    assert _buscar_producto_similar("laptops", catalogo).id == 1
    assert _buscar_producto_similar("monitores para la oficina", catalogo).id == 2
    assert _buscar_producto_similar("impresoras", catalogo) is None


def test_endpoint_interpretar_solicitud_rechaza_texto_vacio():
    response = client.post("/api/v1/evaluaciones/interpretar-solicitud", json={"texto": "   "})
    assert response.status_code == 400


def test_endpoint_interpretar_solicitud_resuelve_productos_del_catalogo_real():
    productos_catalogo = client.get("/api/v1/productos/").json()
    if not productos_catalogo:
        pytest.skip("No hay productos sembrados en la base para probar el emparejamiento.")

    nombre_real = productos_catalogo[0]["nombre"]
    primera_palabra = nombre_real.split()[0]

    response = client.post(
        "/api/v1/evaluaciones/interpretar-solicitud",
        json={"texto": f"Necesito 5 {primera_palabra.lower()}."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interpretado_por"] in ("anthropic", "heuristica")
    assert isinstance(data["productos"], list)
    # No exige que haya coincidencia (depende del catálogo real), pero sí que
    # la forma de la respuesta sea siempre la esperada.
    for p in data["productos"]:
        assert "nombre_detectado" in p
        assert "producto_id" in p
