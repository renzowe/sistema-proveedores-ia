from app.database import SessionLocal, init_db
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.proveedor_producto import ProveedorProducto
from decimal import Decimal

def seed():
    init_db()
    db = SessionLocal()
    try:
        print("[INFO] Iniciando carga de datos de prueba...")

        # 1. Proveedores
        proveedores_data = [
            {
                "razon_social": "TechSupply Perú S.A.C.",
                "ruc": "20601234567",
                "nombre_comercial": "TechSupply",
                "pais": "Perú",
                "ciudad": "Lima",
                "contacto": "Carlos Mendoza",
                "telefono": "+51 987654321",
                "correo": "ventas@techsupply.pe",
                "direccion": "Av. República de Panamá 3500, San Isidro",
                "estado": "Activo"
            },
            {
                "razon_social": "CompuGlobal del Sur S.A.C.",
                "ruc": "20509876543",
                "nombre_comercial": "CompuGlobal",
                "pais": "Perú",
                "ciudad": "Arequipa",
                "contacto": "Mariana Torres",
                "telefono": "+51 954321987",
                "correo": "contacto@compuglobal.pe",
                "direccion": "Calle Mercaderes 120, Arequipa",
                "estado": "Activo"
            },
            {
                "razon_social": "Inversiones Digitales TI S.A.C.",
                "ruc": "20701122334",
                "nombre_comercial": "DigiTech Soluciones",
                "pais": "Perú",
                "ciudad": "Lima",
                "contacto": "Fernando Díaz",
                "telefono": "+51 912345678",
                "correo": "fdiaz@digitech.pe",
                "direccion": "Av. Javier Prado Este 4500, Surco",
                "estado": "Activo"
            },
            {
                "razon_social": "Distribuidora Logística Byte E.I.R.L.",
                "ruc": "10456789012",
                "nombre_comercial": "LogiByte",
                "pais": "Perú",
                "ciudad": "Trujillo",
                "contacto": "Elena Salazar",
                "telefono": "+51 944556677",
                "correo": "ventas@logibyte.pe",
                "direccion": "Jr. Pizarro 540, Trujillo",
                "estado": "Activo"
            }
        ]

        prov_objs = {}
        for p_data in proveedores_data:
            prov = db.query(Proveedor).filter(Proveedor.ruc == p_data["ruc"]).first()
            if not prov:
                prov = Proveedor(**p_data)
                db.add(prov)
                db.flush()
                print(f"  + Proveedor creado: {prov.razon_social}")
            prov_objs[prov.ruc] = prov

        # 2. Productos
        productos_data = [
            {
                "nombre": "Laptop Empresarial 16GB Core i7",
                "codigo": "PROD-LAP-01",
                "descripcion": "Laptop para oficina con 16GB RAM, SSD 512GB, pantalla 15.6 FHD y procesador Intel i7 13va gen.",
                "estado": "Activo"
            },
            {
                "nombre": "Monitor 24 IPS Full HD",
                "codigo": "PROD-MON-01",
                "descripcion": "Monitor LED 24 pulgadas, panel IPS 75Hz, puertos HDMI y DisplayPort con ajuste de altura.",
                "estado": "Activo"
            },
            {
                "nombre": "Teclado Mecánico Ergonómico",
                "codigo": "PROD-TEC-01",
                "descripcion": "Teclado mecánico con switches silenciosos, reposamuñecas acolchado y conexión USB/Bluetooth.",
                "estado": "Activo"
            },
            {
                "nombre": "Mouse Óptico Inalámbrico",
                "codigo": "PROD-MOU-01",
                "descripcion": "Mouse óptico inalámbrico 2.4GHz recargable con sensor de 1600 DPI y botones silenciosos.",
                "estado": "Activo"
            },
            {
                "nombre": "Servidor Rack 1U 32GB Xeon",
                "codigo": "PROD-SRV-01",
                "descripcion": "Servidor empresarial 1U montable en rack con procesador Intel Xeon, 32GB ECC RAM y fuentes redundantes.",
                "estado": "Activo"
            },
            {
                "nombre": "Impresora Multifuncional Láser",
                "codigo": "PROD-IMP-01",
                "descripcion": "Impresora láser monocromática multifunción (impresión, escáner, copia, dúplex automático y Wi-Fi).",
                "estado": "Activo"
            }
        ]

        prod_objs = {}
        for pr_data in productos_data:
            prod = db.query(Producto).filter(Producto.codigo == pr_data["codigo"]).first()
            if not prod:
                prod = Producto(**pr_data)
                db.add(prod)
                db.flush()
                print(f"  + Producto creado: {prod.nombre}")
            prod_objs[prod.codigo] = prod

        # 3. Asignaciones Proveedor - Producto
        relaciones_data = [
            # TechSupply (Equipos premium, rápido pero mayor precio)
            {"ruc": "20601234567", "codigo": "PROD-LAP-01", "precio": Decimal("2850.00"), "tiempo": 4, "cond": "Garantía 2 años en sitio"},
            {"ruc": "20601234567", "codigo": "PROD-MON-01", "precio": Decimal("580.00"), "tiempo": 3, "cond": "Incluye cable HDMI y DP"},
            {"ruc": "20601234567", "codigo": "PROD-TEC-01", "precio": Decimal("160.00"), "tiempo": 2, "cond": "Stock permanente"},
            {"ruc": "20601234567", "codigo": "PROD-SRV-01", "precio": Decimal("8900.00"), "tiempo": 7, "cond": "Instalación incluida"},

            # CompuGlobal (Económico, tiempo de entrega medio)
            {"ruc": "20509876543", "codigo": "PROD-LAP-01", "precio": Decimal("2650.00"), "tiempo": 8, "cond": "Garantía 1 año fabricante"},
            {"ruc": "20509876543", "codigo": "PROD-MON-01", "precio": Decimal("540.00"), "tiempo": 6, "cond": "Flete incluido a nivel nacional"},
            {"ruc": "20509876543", "codigo": "PROD-TEC-01", "precio": Decimal("140.00"), "tiempo": 5, "cond": "Cajas de 10 unidades"},
            {"ruc": "20509876543", "codigo": "PROD-MOU-01", "precio": Decimal("45.00"), "tiempo": 4, "cond": "Empaque individual"},

            # DigiTech (Buen balance calidad/precio)
            {"ruc": "20701122334", "codigo": "PROD-LAP-01", "precio": Decimal("2720.00"), "tiempo": 5, "cond": "Soporte 24/7 primer año"},
            {"ruc": "20701122334", "codigo": "PROD-MON-01", "precio": Decimal("560.00"), "tiempo": 4, "cond": "Descuento por volumen >50 un"},
            {"ruc": "20701122334", "codigo": "PROD-SRV-01", "precio": Decimal("8600.00"), "tiempo": 10, "cond": "Configuración previa sin costo"},
            {"ruc": "20701122334", "codigo": "PROD-IMP-01", "precio": Decimal("1250.00"), "tiempo": 5, "cond": "Incluye tóner de alta capacidad"},

            # LogiByte (Excelente en periféricos e impresoras, tiempos cortos en el norte)
            {"ruc": "10456789012", "codigo": "PROD-TEC-01", "precio": Decimal("135.00"), "tiempo": 3, "cond": "Distribución directa"},
            {"ruc": "10456789012", "codigo": "PROD-MOU-01", "precio": Decimal("40.00"), "tiempo": 2, "cond": "Baterías incluidas"},
            {"ruc": "10456789012", "codigo": "PROD-IMP-01", "precio": Decimal("1180.00"), "tiempo": 4, "cond": "Garantía oficial 1 año"}
        ]

        for rel_data in relaciones_data:
            prov = prov_objs[rel_data["ruc"]]
            prod = prod_objs[rel_data["codigo"]]
            rel = db.query(ProveedorProducto).filter(
                ProveedorProducto.proveedor_id == prov.id,
                ProveedorProducto.producto_id == prod.id
            ).first()
            if not rel:
                rel = ProveedorProducto(
                    proveedor_id=prov.id,
                    producto_id=prod.id,
                    precio=rel_data["precio"],
                    tiempo_entrega_dias=rel_data["tiempo"],
                    condiciones=rel_data["cond"],
                    disponible=True
                )
                db.add(rel)
                print(f"  + Relacion asignada: {prov.razon_social} -> {prod.nombre} (S/ {rel.precio}, {rel.tiempo_entrega_dias} dias)")

        db.commit()
        print("[SUCCESS] Datos de prueba insertados exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al insertar datos: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
