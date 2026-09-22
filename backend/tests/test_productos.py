import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_listar_productos():
    response = client.get("/api/v1/productos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_crear_producto_nombre_vacio():
    payload = {
        "nombre": "   ",
        "codigo": "TEST-EMPTY-01"
    }
    response = client.post("/api/v1/productos/", json=payload)
    assert response.status_code == 400
    assert "vacío" in response.json()["detail"]

def test_crud_producto_y_asignacion():
    cod_test = "TEST-PROD-999"
    ruc_prov = "20888777665"

    # 1. Crear producto
    prod_payload = {
        "nombre": "Producto Test Automatizado",
        "descripcion": "Descripción del producto de prueba",
        "codigo": cod_test,
        "estado": "Activo"
    }
    prod_res = client.post("/api/v1/productos/", json=prod_payload)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 2. Crear proveedor auxiliar
    prov_payload = {
        "razon_social": "Proveedor Auxiliar Test SAC",
        "ruc": ruc_prov,
        "correo": "auxiliar@test.pe"
    }
    prov_res = client.post("/api/v1/proveedores/", json=prov_payload)
    assert prov_res.status_code == 201
    prov_id = prov_res.json()["id"]

    # 3. Asignar producto a proveedor
    rel_payload = {
        "proveedor_id": prov_id,
        "producto_id": prod_id,
        "precio": 1500.50,
        "tiempo_entrega_dias": 3,
        "condiciones": "Entrega inmediata",
        "disponible": True
    }
    rel_res = client.post("/api/v1/proveedor-productos/", json=rel_payload)
    assert rel_res.status_code == 201
    rel_id = rel_res.json()["id"]
    assert float(rel_res.json()["precio"]) == 1500.50

    # 4. Listar relación por producto
    list_rel = client.get(f"/api/v1/proveedor-productos/?producto_id={prod_id}")
    assert list_rel.status_code == 200
    assert len(list_rel.json()) == 1

    # 5. Limpieza
    del_rel = client.delete(f"/api/v1/proveedor-productos/{rel_id}")
    assert del_rel.status_code == 204

    del_prod = client.delete(f"/api/v1/productos/{prod_id}")
    assert del_prod.status_code == 204

    del_prov = client.delete(f"/api/v1/proveedores/{prov_id}")
    assert del_prov.status_code == 204
