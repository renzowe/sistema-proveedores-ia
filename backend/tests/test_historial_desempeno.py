import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_listar_historial():
    response = client.get("/api/v1/historial-desempeno/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_registrar_historial_sin_detalles():
    # Obtener proveedor existente
    prov_res = client.get("/api/v1/proveedores/")
    assert prov_res.status_code == 200
    proveedores = prov_res.json()
    assert len(proveedores) > 0
    prov_id = proveedores[0]["id"]

    payload = {
        "proveedor_id": prov_id,
        "fecha_operacion": "2026-08-01",
        "detalles": []
    }
    response = client.post("/api/v1/historial-desempeno/", json=payload)
    assert response.status_code == 400
    assert "al menos un producto" in response.json()["detail"]

def test_crud_historial_con_detalles_y_metricas():
    # 1. Obtener un proveedor y producto existente
    prov_res = client.get("/api/v1/proveedores/")
    assert prov_res.status_code == 200
    proveedores = prov_res.json()
    assert len(proveedores) > 0
    prov_id = proveedores[0]["id"]

    prod_res = client.get("/api/v1/productos/")
    assert prod_res.status_code == 200
    productos = prod_res.json()
    assert len(productos) > 0
    prod_id = productos[0]["id"]

    # 2. Registrar historial
    hist_payload = {
        "proveedor_id": prov_id,
        "fecha_operacion": "2026-07-20",
        "tiempo_entrega_promedio_dias": 4,
        "cumplimiento_porcentaje": 95.5,
        "observaciones": "Prueba de historial automatizada",
        "detalles": [
            {
                "producto_id": prod_id,
                "cantidad_solicitada": 100,
                "cantidad_entregada": 100,
                "porcentaje_defectos": 0.5,
                "observaciones": "Entrega perfecta de prueba"
            }
        ]
    }
    create_res = client.post("/api/v1/historial-desempeno/", json=hist_payload)
    assert create_res.status_code == 201
    hist_id = create_res.json()["id"]
    assert len(create_res.json()["detalles"]) == 1

    # 3. Obtener por ID
    get_res = client.get(f"/api/v1/historial-desempeno/{hist_id}")
    assert get_res.status_code == 200
    assert get_res.json()["proveedor_id"] == prov_id

    # 4. Obtener métricas del proveedor
    metrics_res = client.get(f"/api/v1/historial-desempeno/proveedor/{prov_id}/metricas")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "cumplimiento_promedio" in metrics
    assert "tasa_defectos_promedio" in metrics
    assert metrics["total_operaciones"] > 0

    # 5. Obtener historial por producto
    prod_hist_res = client.get(f"/api/v1/historial-desempeno/producto/{prod_id}")
    assert prod_hist_res.status_code == 200
    assert isinstance(prod_hist_res.json(), list)

    # 6. Eliminar el historial de prueba
    del_res = client.delete(f"/api/v1/historial-desempeno/{hist_id}")
    assert del_res.status_code == 204
