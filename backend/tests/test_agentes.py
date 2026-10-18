import pytest
from fastapi.testclient import TestClient

from app.agents import (
    AgenteCalidad,
    AgenteDecisor,
    AgenteFinanciero,
    AgenteLogistico,
    AgenteRiesgo,
    OrquestadorAgentes,
)
from app.main import app

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
        {
            "proveedor_id": 1,
            "razon_social": "Prov Rapido",
            "tiempo_entrega_max_dias": 3,
            "cumple_plazo_maximo": True,
        },
        {
            "proveedor_id": 2,
            "razon_social": "Prov Lento",
            "tiempo_entrega_max_dias": 10,
            "cumple_plazo_maximo": False,
        },
    ]
    res = agente.analizar(candidatos, min_tiempo_global=3, entrega_maxima_dias=5)
    assert len(res) == 2
    assert res[0]["puntaje_logistica"] == 100.0
    assert res[1]["cumple_plazo_maximo"] is False
    assert "DESTACADO" in res[0]["dictamen_logistico"]
    assert "DESFAVORABLE" in res[1]["dictamen_logistico"]


def _decidir(proveedores, prioridad="precio"):
    """proveedores: lista de (id, nombre, cobertura_total, faltantes, puntaje_uniforme)."""
    candidatos, fin, cal, log, rie = [], [], [], [], []
    for prov_id, nombre, completa, faltantes, p in proveedores:
        candidatos.append({
            "proveedor_id": prov_id, "razon_social": nombre, "ruc": str(prov_id),
            "costo_total": 1000.0, "tiempo_entrega_max_dias": 3,
            "cobertura_porcentaje": 100.0 if completa else 50.0,
            "es_cobertura_total": completa,
            "productos_faltantes": [{"nombre_producto": f} for f in faltantes],
        })
        fin.append({"proveedor_id": prov_id, "puntaje_precio": p, "dictamen_financiero": ""})
        cal.append({"proveedor_id": prov_id, "puntaje_calidad": p, "dictamen_calidad": ""})
        log.append({"proveedor_id": prov_id, "puntaje_logistica": p, "dictamen_logistico": ""})
        rie.append({"proveedor_id": prov_id, "puntaje_historial": p, "puntaje_riesgo": p,
                    "cumplimiento_historico_pct": 95.0, "dictamen_riesgo": ""})
    return AgenteDecisor().decidir(candidatos, fin, cal, log, rie, prioridad)


def test_decisor_no_recomienda_cobertura_parcial_si_otro_cubre_todo():
    res = _decidir([
        (1, "Cubre Todo", True, [], 80.0),
        (2, "Cubre la Mitad", False, ["Mouse"], 100.0),
    ])
    ranking = res["ranking"]

    # El ranking sigue ordenado por puntaje: el parcial queda primero...
    assert ranking[0]["razon_social"] == "Cubre la Mitad"
    # ...pero el recomendado es el que cubre el pedido completo.
    assert res["proveedor_recomendado"]["razon_social"] == "Cubre Todo"
    assert [r["recomendado"] for r in ranking] == [False, True]
    assert ranking[0]["cobertura_completa"] is False
    assert ranking[0]["productos_faltantes"] == ["Mouse"]
    assert ranking[0]["explicacion"].startswith("No recomendable por cobertura parcial")
    assert "no ofrece todos los productos" in res["conclusion_agente_decisor"]


def test_decisor_sin_cobertura_total_recomienda_mayor_puntaje_y_advierte():
    res = _decidir([
        (1, "Parcial A", False, ["Mouse"], 70.0),
        (2, "Parcial B", False, ["Teclado"], 90.0),
    ])
    assert res["proveedor_recomendado"]["razon_social"] == "Parcial B"
    assert "compras complementarias para: Teclado" in res["conclusion_agente_decisor"]


def test_flujo_cobertura_parcial_no_gana_aunque_tenga_mas_puntaje(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "LLM_ENABLED", False)  # explicación en modo demostración

    creados = {"proveedores": [], "productos": [], "relaciones": []}
    eval_id = None
    try:
        for codigo, nombre in (("TEST-COB-P1", "Producto Cobertura Uno"), ("TEST-COB-P2", "Producto Cobertura Dos")):
            r = client.post("/api/v1/productos/", json={"nombre": nombre, "codigo": codigo, "estado": "Activo"})
            assert r.status_code == 201
            creados["productos"].append(r.json()["id"])
        p1, p2 = creados["productos"]

        for ruc, nombre in (("20999111001", "Cobertura Completa SAC"), ("20999111002", "Cobertura Parcial SAC")):
            r = client.post("/api/v1/proveedores/", json={"razon_social": nombre, "ruc": ruc, "estado": "Activo"})
            assert r.status_code == 201
            creados["proveedores"].append(r.json()["id"])
        completo, parcial = creados["proveedores"]

        ofertas = [
            (completo, p1, 300.0, 9), (completo, p2, 300.0, 9),  # todo, pero caro y lento
            (parcial, p1, 100.0, 2),                             # solo P1, barato y rápido
        ]
        for prov, prod, precio, dias in ofertas:
            r = client.post("/api/v1/proveedor-productos/", json={
                "proveedor_id": prov, "producto_id": prod, "precio": precio,
                "tiempo_entrega_dias": dias, "disponible": True,
            })
            assert r.status_code == 201
            creados["relaciones"].append(r.json()["id"])

        r = client.post("/api/v1/evaluaciones/", json={
            "titulo": "Prueba de cobertura parcial", "prioridad": "precio",
            "productos": [{"producto_id": p1, "cantidad": 10}, {"producto_id": p2, "cantidad": 10}],
        })
        assert r.status_code == 201
        eval_id = r.json()["id"]

        proc = client.post(f"/api/v1/evaluaciones/{eval_id}/procesar").json()
        por_id = {x["proveedor_id"]: x for x in proc["ranking"]}
        assert por_id[parcial]["puntajes"]["final"] > por_id[completo]["puntajes"]["final"]
        assert proc["proveedor_recomendado"]["proveedor_id"] == completo

        # Lo persistido coincide con la decisión.
        guardados = client.get(f"/api/v1/evaluaciones/{eval_id}/resultados").json()
        assert next(x for x in guardados["ranking"] if x["recomendado"])["proveedor_id"] == completo

        # El asistente (modo demostración) explica por qué no ganó el de más puntaje.
        chat = client.post("/api/v1/evaluaciones/asistente/mensaje", json={
            "mensajes": [{"rol": "usuario", "contenido": "¿Por qué no ganó el de más puntaje?"}],
            "evaluacion_id": eval_id,
        }).json()
        assert "Cobertura Completa SAC" in chat["respuesta"]
        assert "no puede recomendarse" in chat["respuesta"]
        assert "Producto Cobertura Dos" in chat["respuesta"]
    finally:
        if eval_id:
            client.delete(f"/api/v1/evaluaciones/{eval_id}")
        for rel_id in creados["relaciones"]:
            client.delete(f"/api/v1/proveedor-productos/{rel_id}")
        for prov_id in creados["proveedores"]:
            client.delete(f"/api/v1/proveedores/{prov_id}")
        for prod_id in creados["productos"]:
            client.delete(f"/api/v1/productos/{prod_id}")


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
            {"producto_id": p2["id"], "cantidad": 15},
        ],
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
