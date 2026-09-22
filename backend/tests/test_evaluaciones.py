import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_listar_evaluaciones():
    response = client.get("/api/v1/evaluaciones/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_crear_evaluacion_sin_productos():
    payload = {
        "titulo": "Evaluación sin productos",
        "productos": []
    }
    response = client.post("/api/v1/evaluaciones/", json=payload)
    assert response.status_code == 400
    assert "al menos un producto" in response.json()["detail"]

def test_crud_evaluacion_y_proveedores_compatibles():
    # 1. Obtener productos del catálogo
    prod_res = client.get("/api/v1/productos/")
    assert prod_res.status_code == 200
    productos = prod_res.json()
    assert len(productos) >= 2
    p1 = productos[0]
    p2 = productos[1]

    # 2. Crear solicitud de evaluación
    eval_payload = {
        "titulo": "Adquisición de Equipos para Nueva Sede",
        "descripcion_necesidad": "Se requieren 20 laptops y 20 monitores para área comercial.",
        "entrega_maxima_dias": 7,
        "prioridad": "calidad",
        "estado": "Pendiente",
        "productos": [
            {
                "producto_id": p1["id"],
                "cantidad": 20,
                "especificaciones": "16GB RAM mínimo"
            },
            {
                "producto_id": p2["id"],
                "cantidad": 20,
                "especificaciones": "Panel IPS antirreflejo"
            }
        ]
    }
    create_res = client.post("/api/v1/evaluaciones/", json=eval_payload)
    assert create_res.status_code == 201
    eval_id = create_res.json()["id"]
    assert len(create_res.json()["productos_solicitados"]) == 2

    # 3. Obtener por ID
    get_res = client.get(f"/api/v1/evaluaciones/{eval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["titulo"] == eval_payload["titulo"]

    # 4. Buscar proveedores compatibles
    compat_res = client.get(f"/api/v1/evaluaciones/{eval_id}/proveedores-compatibles")
    assert compat_res.status_code == 200
    compat_data = compat_res.json()
    assert "proveedores_compatibles" in compat_data
    assert compat_data["total_productos_solicitados"] == 2
    assert len(compat_data["proveedores_compatibles"]) > 0

    primer_prov = compat_data["proveedores_compatibles"][0]
    assert "proveedor_id" in primer_prov
    assert "cobertura_porcentaje" in primer_prov
    assert "costo_total" in primer_prov
    assert "tiempo_entrega_max_dias" in primer_prov
    assert "cumple_plazo_maximo" in primer_prov

    # 5. Eliminar la evaluación de prueba
    del_res = client.delete(f"/api/v1/evaluaciones/{eval_id}")
    assert del_res.status_code == 204

def test_motor_de_evaluacion_multicriterio():
    # 1. Obtener productos de prueba (Laptop y Monitor)
    prod_res = client.get("/api/v1/productos/")
    assert prod_res.status_code == 200
    productos = prod_res.json()
    p_lap = next((p for p in productos if "Laptop" in p["nombre"]), productos[0])
    p_mon = next((p for p in productos if "Monitor" in p["nombre"]), productos[1])

    # 2. Crear evaluación con prioridad calidad
    eval_payload = {
        "titulo": "Evaluación Automatizada de Motor Multicriterio",
        "descripcion_necesidad": "Compra de 10 Laptops y 10 Monitores",
        "entrega_maxima_dias": 6,
        "prioridad": "calidad",
        "productos": [
            {"producto_id": p_lap["id"], "cantidad": 10},
            {"producto_id": p_mon["id"], "cantidad": 10}
        ]
    }
    create_res = client.post("/api/v1/evaluaciones/", json=eval_payload)
    assert create_res.status_code == 201
    eval_id = create_res.json()["id"]

    # 3. Procesar evaluación con el motor
    process_res = client.post(f"/api/v1/evaluaciones/{eval_id}/procesar")
    assert process_res.status_code == 200
    proc_data = process_res.json()

    assert proc_data["estado"] == "Procesada"
    assert "proveedor_recomendado" in proc_data
    assert proc_data["proveedor_recomendado"] is not None
    assert "puntajes" in proc_data["proveedor_recomendado"]
    assert "final" in proc_data["proveedor_recomendado"]["puntajes"]
    assert len(proc_data["ranking"]) > 0

    # 4. Consultar resultados persistidos
    res_get = client.get(f"/api/v1/evaluaciones/{eval_id}/resultados")
    assert res_get.status_code == 200
    res_data = res_get.json()
    assert res_data["estado"] == "Procesada"
    assert len(res_data["ranking"]) > 0
    assert any(r["recomendado"] for r in res_data["ranking"])

    # Validar que los campos de cada criterio existan
    ganador = next(r for r in res_data["ranking"] if r["recomendado"])
    assert ganador["puntaje_precio"] > 0
    assert ganador["puntaje_calidad"] > 0
    assert ganador["puntaje_final"] > 0
    assert "PROVEEDOR RECOMENDADO" in ganador["explicacion"]

    # 5. Limpiar
    del_res = client.delete(f"/api/v1/evaluaciones/{eval_id}")
    assert del_res.status_code == 204
