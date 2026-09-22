import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agents import (
    AgenteFinanciero,
    AgenteCalidad,
    AgenteLogistico,
    AgenteRiesgo,
    AgenteDecisor,
    OrquestadorAgentes
)

client = TestClient(app)

def test_agente_financiero():
    agente = AgenteFinanciero()
    candidatos = [
        {"proveedor_id": 1, "razon_social": "Prov Barato", "costo_total": 1000.0},
        {"proveedor_id": 2, "razon_social": "Prov Caro", "costo_total": 2000.0},
    ]
    res = agente.analizar(candidatos, min_costo_global=1000.0)
    assert len(res) == 2
    assert res[0]["puntaje_precio"] == 100.0
    assert res[0]["es_mas_economico"] is True
    assert res[1]["puntaje_precio"] == 50.0
    assert "FAVORABLE" in res[0]["dictamen_financiero"]

def test_agente_calidad():
    agente = AgenteCalidad()
    candidatos = [
        {"proveedor_id": 1, "razon_social": "Prov Alta Calidad"},
        {"proveedor_id": 2, "razon_social": "Prov Con Defectos"},
    ]
    metricas = {
        1: {"tasa_defectos_promedio": 0.0, "total_operaciones": 3},
        2: {"tasa_defectos_promedio": 4.0, "total_operaciones": 2},
    }
    res = agente.analizar(candidatos, metricas)
    assert len(res) == 2
    assert res[0]["puntaje_calidad"] == 100.0
    assert res[1]["puntaje_calidad"] == 40.0
    assert "EXCELENTE" in res[0]["dictamen_calidad"]
    assert "ALERTA" in res[1]["dictamen_calidad"]

def test_agente_logistico():
    agente = AgenteLogistico()
    candidatos = [
        {"proveedor_id": 1, "razon_social": "Prov Rapido", "tiempo_entrega_max_dias": 3, "cumple_plazo_maximo": True},
        {"proveedor_id": 2, "razon_social": "Prov Lento", "tiempo_entrega_max_dias": 10, "cumple_plazo_maximo": False},
    ]
    res = agente.analizar(candidatos, min_tiempo_global=3, entrega_maxima_dias=5)
    assert len(res) == 2
    assert res[0]["puntaje_logistica"] == 100.0
    assert res[1]["cumple_plazo_maximo"] is False
    assert "DESTACADO" in res[0]["dictamen_logistico"]
    assert "DESFAVORABLE" in res[1]["dictamen_logistico"]

def test_orquestador_y_endpoint_informe_agentes():
    # 1. Obtener productos de prueba
    prod_res = client.get("/api/v1/productos/")
    assert prod_res.status_code == 200
    productos = prod_res.json()
    p1 = productos[0]
    p2 = productos[1]

    # 2. Crear evaluacion
    eval_payload = {
        "titulo": "Prueba de Orquestación Agéntica",
        "descripcion_necesidad": "Test para orquestador y agentes especializados",
        "entrega_maxima_dias": 5,
        "prioridad": "balanceado",
        "productos": [
            {"producto_id": p1["id"], "cantidad": 15},
            {"producto_id": p2["id"], "cantidad": 15}
        ]
    }
    create_res = client.post("/api/v1/evaluaciones/", json=eval_payload)
    assert create_res.status_code == 201
    eval_id = create_res.json()["id"]

    # 3. Procesar evaluacion (ejecuta el orquestador internamente)
    proc_res = client.post(f"/api/v1/evaluaciones/{eval_id}/procesar")
    assert proc_res.status_code == 200
    assert proc_res.json()["estado"] == "Procesada"
    assert "conclusion_ejecutiva" in proc_res.json()

    # 4. Obtener informe agéntico detallado
    informe_res = client.get(f"/api/v1/evaluaciones/{eval_id}/informe-agentes")
    assert informe_res.status_code == 200
    informe_data = informe_res.json()
    assert informe_data["estado_orquestacion"] == "Completada"
    assert len(informe_data["agentes_participantes"]) == 5
    assert "detalles_agentes" in informe_data
    assert "financiero" in informe_data["detalles_agentes"]
    assert "calidad" in informe_data["detalles_agentes"]
    assert "logistico" in informe_data["detalles_agentes"]
    assert "riesgo" in informe_data["detalles_agentes"]

    # 5. Limpieza
    del_res = client.delete(f"/api/v1/evaluaciones/{eval_id}")
    assert del_res.status_code == 204
