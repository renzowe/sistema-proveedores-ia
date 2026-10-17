"""
Fase 12 (subfases "borrador compartido y conversación" + "explicación de
resultados") — Pruebas del asistente conversacional (`/evaluaciones/asistente/mensaje`).

Con `LLM_ENABLED=false` (configuración por defecto de este repo, sin
`ANTHROPIC_API_KEY`), todas estas pruebas ejercitan el "modo demostración":
el endpoint sigue funcionando end-to-end, sin llamadas externas, usando el
parser heurístico ya existente (armar borrador) o una plantilla basada en
datos reales ya persistidos (explicar resultados). El modo real se prueba
aparte, gateado por `LLM_REALMENTE_DISPONIBLE` (se salta sin credenciales).
"""

import pytest
from fastapi.testclient import TestClient

from app.ai.llm_client import LLMClient
from app.config import settings
from app.main import app

client = TestClient(app)

LLM_REALMENTE_DISPONIBLE = LLMClient().esta_disponible()

ENDPOINT = "/api/v1/evaluaciones/asistente/mensaje"


def _mensaje(texto, borrador=None, evaluacion_id=None):
    payload = {"mensajes": [{"rol": "usuario", "contenido": texto}]}
    if borrador is not None:
        payload["borrador"] = borrador
    if evaluacion_id is not None:
        payload["evaluacion_id"] = evaluacion_id
    return payload


def test_estado_asistente_informa_modo_demostracion_sin_credenciales(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    response = client.get("/api/v1/evaluaciones/asistente/estado")
    assert response.status_code == 200
    assert response.json()["modo"] == "demostracion"


# --- Modo "armar borrador" (sin evaluacion_id) ------------------------------

def test_asistente_demostracion_extrae_productos_prioridad_y_plazo():
    response = client.post(ENDPOINT, json=_mensaje(
        "Necesito 15 laptops y 10 monitores, priorizando calidad, entrega en maximo 12 dias."
    ))
    assert response.status_code == 200
    data = response.json()

    assert data["modo"] == "demostracion"
    assert "[Modo demostración" in data["respuesta"]

    borrador = data["borrador"]
    assert borrador["prioridad"] == "calidad"
    assert borrador["entrega_maxima_dias"] == 12
    nombres_cantidades = {p["nombre_detectado"]: p["cantidad"] for p in borrador["productos"]}
    assert nombres_cantidades.get("laptops") == 15
    assert nombres_cantidades.get("monitores") == 10
    assert "productos" in data["campos_actualizados"]


def test_asistente_demostracion_sin_productos_pide_completar_datos():
    response = client.post(ENDPOINT, json=_mensaje("Hola, buenos días."))
    assert response.status_code == 200
    data = response.json()

    assert data["modo"] == "demostracion"
    assert data["listo_para_confirmar"] is False
    assert data["borrador"]["productos"] == []
    assert "falta" in data["respuesta"].lower()


def test_asistente_demostracion_no_pisa_titulo_ya_definido_manualmente():
    borrador_previo = {
        "titulo": "Compra de equipos de oficina",
        "prioridad": "balanceado",
        "productos": [],
    }
    response = client.post(ENDPOINT, json=_mensaje(
        "También necesito 5 sillas ergonómicas.", borrador=borrador_previo
    ))
    assert response.status_code == 200
    data = response.json()

    assert data["borrador"]["titulo"] == "Compra de equipos de oficina"
    nombres = [p["nombre_detectado"] for p in data["borrador"]["productos"]]
    assert "sillas ergonómicas" in nombres


def test_asistente_rechaza_mensaje_en_blanco():
    response = client.post(ENDPOINT, json=_mensaje("   "))
    assert response.status_code == 400


def test_asistente_rechaza_lista_de_mensajes_vacia():
    response = client.post(ENDPOINT, json={"mensajes": []})
    assert response.status_code == 400


def test_asistente_rechaza_rol_invalido():
    response = client.post(ENDPOINT, json={"mensajes": [{"rol": "sistema", "contenido": "hola"}]})
    assert response.status_code == 422


# --- Modo "explicar resultados" (con evaluacion_id) -------------------------

def test_asistente_evaluacion_id_inexistente_devuelve_404():
    response = client.post(ENDPOINT, json=_mensaje("Explícame el resultado.", evaluacion_id=999999999))
    assert response.status_code == 404


def test_asistente_explica_evaluacion_no_procesada_sin_inventar_resultado():
    prov_res = client.post("/api/v1/proveedores/", json={
        "razon_social": "Asistente Test Proveedor No Procesada SAC",
        "ruc": "20888000001",
        "ciudad": "Lima",
        "contacto": "QA Automatizado",
        "correo": "qa@asistente-test.pe",
        "estado": "Activo",
    })
    assert prov_res.status_code == 201
    prov_id = prov_res.json()["id"]

    prod_res = client.post("/api/v1/productos/", json={
        "nombre": "Producto Asistente Test No Procesada",
        "codigo": "TEST-ASISTENTE-01",
        "estado": "Activo",
    })
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    eval_res = client.post("/api/v1/evaluaciones/", json={
        "titulo": "Evaluación sin procesar para el asistente",
        "prioridad": "balanceado",
        "productos": [{"producto_id": prod_id, "cantidad": 1}],
    })
    assert eval_res.status_code == 201
    eval_id = eval_res.json()["id"]

    try:
        response = client.post(ENDPOINT, json=_mensaje("Explícame el resultado.", evaluacion_id=eval_id))
        assert response.status_code == 200
        data = response.json()
        assert data["listo_para_confirmar"] is False
        assert "no ha sido procesada" in data["respuesta"]
    finally:
        client.delete(f"/api/v1/evaluaciones/{eval_id}")
        client.delete(f"/api/v1/productos/{prod_id}")
        client.delete(f"/api/v1/proveedores/{prov_id}")


def test_asistente_explica_evaluacion_procesada_usando_datos_reales():
    prov_res = client.post("/api/v1/proveedores/", json={
        "razon_social": "Asistente Test Proveedor Procesada SAC",
        "ruc": "20888000002",
        "ciudad": "Lima",
        "contacto": "QA Automatizado",
        "correo": "qa2@asistente-test.pe",
        "estado": "Activo",
    })
    assert prov_res.status_code == 201
    prov_id = prov_res.json()["id"]

    prod_res = client.post("/api/v1/productos/", json={
        "nombre": "Producto Asistente Test Procesada",
        "codigo": "TEST-ASISTENTE-02",
        "estado": "Activo",
    })
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    rel_res = client.post("/api/v1/proveedor-productos/", json={
        "proveedor_id": prov_id,
        "producto_id": prod_id,
        "precio": 100.0,
        "tiempo_entrega_dias": 3,
        "disponible": True,
    })
    assert rel_res.status_code == 201
    rel_id = rel_res.json()["id"]

    eval_res = client.post("/api/v1/evaluaciones/", json={
        "titulo": "Evaluación procesada para el asistente",
        "prioridad": "balanceado",
        "productos": [{"producto_id": prod_id, "cantidad": 10}],
    })
    assert eval_res.status_code == 201
    eval_id = eval_res.json()["id"]

    try:
        proc_res = client.post(f"/api/v1/evaluaciones/{eval_id}/procesar")
        assert proc_res.status_code == 200

        response = client.post(ENDPOINT, json=_mensaje("¿Por qué ganó este proveedor?", evaluacion_id=eval_id))
        assert response.status_code == 200
        data = response.json()

        assert data["modo"] == "demostracion"
        assert data["contexto_evaluacion_id"] == eval_id
        assert "Asistente Test Proveedor Procesada SAC" in data["respuesta"]
        assert "[Modo demostración" in data["respuesta"]
    finally:
        client.delete(f"/api/v1/evaluaciones/{eval_id}")
        client.delete(f"/api/v1/proveedor-productos/{rel_id}")
        client.delete(f"/api/v1/productos/{prod_id}")
        client.delete(f"/api/v1/proveedores/{prov_id}")


# --- Modo real (gateado; se salta sin ANTHROPIC_API_KEY configurada) --------

@pytest.mark.skipif(not LLM_REALMENTE_DISPONIBLE, reason="Requiere LLM_ENABLED=true y ANTHROPIC_API_KEY configurada")
def test_asistente_modo_real_responde_sin_romper_el_contrato():
    response = client.post(ENDPOINT, json=_mensaje("Necesito 3 laptops para el área de ventas."))
    assert response.status_code == 200
    data = response.json()
    assert data["modo"] in ("real", "demostracion")
    assert isinstance(data["respuesta"], str) and data["respuesta"]
