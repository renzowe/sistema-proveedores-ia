import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_listar_proveedores():
    response = client.get("/api/v1/proveedores/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_crear_proveedor_invalido_ruc():
    # RUC con formato incorrecto
    payload = {
        "razon_social": "Empresa Test Invalida SAC",
        "ruc": "12345",
        "correo": "test@empresa.com"
    }
    response = client.post("/api/v1/proveedores/", json=payload)
    assert response.status_code == 400
    assert "11 dígitos" in response.json()["detail"]

def test_crear_proveedor_correo_invalido():
    payload = {
        "razon_social": "Empresa Test Correo SAC",
        "ruc": "20999888771",
        "correo": "correo-sin-formato"
    }
    response = client.post("/api/v1/proveedores/", json=payload)
    assert response.status_code == 400
    assert "correo" in response.json()["detail"]

def test_crud_proveedor():
    ruc_test = "20999000111"
    
    # 1. Crear
    payload = {
        "razon_social": "Proveedor de Pruebas Unitarias SAC",
        "ruc": ruc_test,
        "nombre_comercial": "TestProveedor",
        "pais": "Perú",
        "ciudad": "Lima",
        "contacto": "Juan Pérez",
        "telefono": "+51 999888777",
        "correo": "juan.perez@testproveedor.pe",
        "direccion": "Av. Las Flores 123",
        "estado": "Activo"
    }
    create_res = client.post("/api/v1/proveedores/", json=payload)
    assert create_res.status_code == 201
    prov_id = create_res.json()["id"]
    assert create_res.json()["ruc"] == ruc_test

    # 2. Obtener por ID
    get_res = client.get(f"/api/v1/proveedores/{prov_id}")
    assert get_res.status_code == 200
    assert get_res.json()["razon_social"] == payload["razon_social"]

    # 3. Actualizar
    update_payload = {
        "nombre_comercial": "TestProveedor Actualizado",
        "telefono": "+51 911222333"
    }
    put_res = client.put(f"/api/v1/proveedores/{prov_id}", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["nombre_comercial"] == "TestProveedor Actualizado"

    # 4. Eliminar
    del_res = client.delete(f"/api/v1/proveedores/{prov_id}")
    assert del_res.status_code == 204

    # 5. Verificar 404
    get_deleted = client.get(f"/api/v1/proveedores/{prov_id}")
    assert get_deleted.status_code == 404
