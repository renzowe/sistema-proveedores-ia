"""
Fase 13 — Pruebas y cierre del MVP.

A diferencia de los tests existentes (que verifican cada módulo con datos
auxiliares independientes), este archivo encadena el flujo COMPLETO del MVP
usando el mismo proveedor y producto de punta a punta:

    proveedor -> producto -> catálogo (proveedor-producto) -> historial de
    desempeño -> evaluación -> proveedores compatibles -> procesamiento
    (motor determinístico + agentes) -> resultados -> informe de agentes
    -> persistencia real en PostgreSQL -> limpieza.

Objetivo: demostrar que el flujo descrito en "Definición del MVP terminado"
de `PLAN_IMPLEMENTACION.md` funciona de extremo a extremo, en modo 100%
determinístico (`LLM_ENABLED=false`), sin depender de Claude ni de una
API Key de Anthropic.
"""

from app.config import settings
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_flujo_completo_mvp_de_extremo_a_extremo_sin_llm():
    # --- 0. Precondición: el MVP debe operar en modo determinístico puro ---
    assert settings.LLM_ENABLED is False, (
        "F13 debe ejecutarse con LLM_ENABLED=false: el cierre del MVP no "
        "depende de Claude ni de una API Key de Anthropic."
    )

    ruc_test = "20777123456"
    codigo_producto = "TEST-CIERRE-MVP-01"

    # --- 1. Crear proveedor ---
    prov_payload = {
        "razon_social": "Cierre MVP Proveedor de Pruebas SAC",
        "ruc": ruc_test,
        "ciudad": "Lima",
        "contacto": "QA Automatizado",
        "correo": "qa@cierre-mvp-test.pe",
        "estado": "Activo",
    }
    prov_res = client.post("/api/v1/proveedores/", json=prov_payload)
    assert prov_res.status_code == 201
    prov_id = prov_res.json()["id"]

    # --- 2. Crear producto ---
    prod_payload = {
        "nombre": "Producto de Cierre de MVP",
        "descripcion": "Producto usado exclusivamente para la prueba de cierre F13",
        "codigo": codigo_producto,
        "estado": "Activo",
    }
    prod_res = client.post("/api/v1/productos/", json=prod_payload)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # --- 3. Asociar proveedor y producto (catálogo comercial) ---
    rel_payload = {
        "proveedor_id": prov_id,
        "producto_id": prod_id,
        "precio": 500.00,
        "tiempo_entrega_dias": 5,
        "condiciones": "Prueba automatizada de cierre",
        "disponible": True,
    }
    rel_res = client.post("/api/v1/proveedor-productos/", json=rel_payload)
    assert rel_res.status_code == 201
    rel_id = rel_res.json()["id"]

    # --- 4. Registrar historial de desempeño ---
    hist_payload = {
        "proveedor_id": prov_id,
        "fecha_operacion": "2026-06-15",
        "tiempo_entrega_promedio_dias": 4,
        "cumplimiento_porcentaje": 98.0,
        "observaciones": "Historial de cierre de MVP (F13)",
        "detalles": [
            {
                "producto_id": prod_id,
                "cantidad_solicitada": 50,
                "cantidad_entregada": 50,
                "porcentaje_defectos": 0.0,
                "observaciones": "Entrega conforme",
            }
        ],
    }
    hist_res = client.post("/api/v1/historial-desempeno/", json=hist_payload)
    assert hist_res.status_code == 201
    hist_id = hist_res.json()["id"]

    metricas_res = client.get(f"/api/v1/historial-desempeno/proveedor/{prov_id}/metricas")
    assert metricas_res.status_code == 200
    assert metricas_res.json()["total_operaciones"] == 1

    # --- 5. Crear evaluación (uno o varios productos) ---
    eval_payload = {
        "titulo": "Evaluación de Cierre de MVP (F13)",
        "descripcion_necesidad": "Prueba de regresión de extremo a extremo",
        "entrega_maxima_dias": 10,
        "prioridad": "balanceado",
        "productos": [
            {"producto_id": prod_id, "cantidad": 20, "especificaciones": "Sin observaciones"},
        ],
    }
    eval_res = client.post("/api/v1/evaluaciones/", json=eval_payload)
    assert eval_res.status_code == 201
    eval_id = eval_res.json()["id"]
    assert len(eval_res.json()["productos_solicitados"]) == 1

    # --- 6. Buscar proveedores compatibles ---
    compat_res = client.get(f"/api/v1/evaluaciones/{eval_id}/proveedores-compatibles")
    assert compat_res.status_code == 200
    compat_data = compat_res.json()
    assert compat_data["total_proveedores_compatibles"] >= 1
    proveedor_compatible = next(
        p for p in compat_data["proveedores_compatibles"] if p["proveedor_id"] == prov_id
    )
    assert proveedor_compatible["es_cobertura_total"] is True
    assert proveedor_compatible["cumple_plazo_maximo"] is True

    # --- 7. Procesar evaluación (motor determinístico + agentes) ---
    proc_res = client.post(f"/api/v1/evaluaciones/{eval_id}/procesar")
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["estado"] == "Procesada"
    assert proc_data["proveedor_recomendado"] is not None
    assert proc_data["proveedor_recomendado"]["proveedor_id"] == prov_id
    assert proc_data["proveedor_recomendado"]["puntajes"]["final"] > 0

    # --- 8. Obtener resultados persistidos (nueva lectura independiente) ---
    resultados_res = client.get(f"/api/v1/evaluaciones/{eval_id}/resultados")
    assert resultados_res.status_code == 200
    resultados_data = resultados_res.json()
    assert resultados_data["estado"] == "Procesada"
    ganador = next(r for r in resultados_data["ranking"] if r["recomendado"])
    assert ganador["proveedor_id"] == prov_id
    assert ganador["puntaje_final"] > 0
    assert ganador["puntaje_historial"] > 0  # confirma que el historial registrado impactó el cálculo

    # --- 9. Obtener el informe agéntico (dictámenes de los 5 agentes) ---
    informe_res = client.get(f"/api/v1/evaluaciones/{eval_id}/informe-agentes")
    assert informe_res.status_code == 200
    informe_data = informe_res.json()
    assert informe_data["estado_orquestacion"] == "Completada"
    assert len(informe_data["agentes_participantes"]) == 5
    for dominio in ("financiero", "calidad", "logistico", "riesgo"):
        assert dominio in informe_data["detalles_agentes"]
    assert informe_data["proveedor_recomendado"]["proveedor_id"] == prov_id

    # --- 10. Verificar persistencia real: una lectura nueva ve el mismo resultado ---
    eval_persistida = client.get(f"/api/v1/evaluaciones/{eval_id}")
    assert eval_persistida.status_code == 200
    assert eval_persistida.json()["estado"] == "Procesada"
    assert len(eval_persistida.json()["detalles_resultado"]) >= 1

    # --- 11. Limpieza (orden inverso de dependencias) ---
    assert client.delete(f"/api/v1/evaluaciones/{eval_id}").status_code == 204
    assert client.delete(f"/api/v1/historial-desempeno/{hist_id}").status_code == 204
    assert client.delete(f"/api/v1/proveedor-productos/{rel_id}").status_code == 204
    assert client.delete(f"/api/v1/productos/{prod_id}").status_code == 204
    assert client.delete(f"/api/v1/proveedores/{prov_id}").status_code == 204

    # --- 12. Confirmar que la limpieza persistió realmente en PostgreSQL ---
    assert client.get(f"/api/v1/evaluaciones/{eval_id}").status_code == 404
    assert client.get(f"/api/v1/proveedores/{prov_id}").status_code == 404
