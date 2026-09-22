from datetime import date
from decimal import Decimal
from app.database import SessionLocal, init_db
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.historial_desempeno import HistorialDesempeno
from app.models.historial_desempeno_detalle import HistorialDesempenoDetalle

def seed_historial():
    init_db()
    db = SessionLocal()
    try:
        print("[INFO] Iniciando carga de historial de desempeno...")

        # Obtener proveedores
        p_tech = db.query(Proveedor).filter(Proveedor.ruc == "20601234567").first() # TechSupply
        p_compu = db.query(Proveedor).filter(Proveedor.ruc == "20509876543").first() # CompuGlobal
        p_digi = db.query(Proveedor).filter(Proveedor.ruc == "20701122334").first() # DigiTech
        p_logi = db.query(Proveedor).filter(Proveedor.ruc == "10456789012").first() # LogiByte

        # Obtener productos
        prod_lap = db.query(Producto).filter(Producto.codigo == "PROD-LAP-01").first()
        prod_mon = db.query(Producto).filter(Producto.codigo == "PROD-MON-01").first()
        prod_tec = db.query(Producto).filter(Producto.codigo == "PROD-TEC-01").first()
        prod_mou = db.query(Producto).filter(Producto.codigo == "PROD-MOU-01").first()
        prod_srv = db.query(Producto).filter(Producto.codigo == "PROD-SRV-01").first()
        prod_imp = db.query(Producto).filter(Producto.codigo == "PROD-IMP-01").first()

        if not (p_tech and p_compu and p_digi and p_logi and prod_lap and prod_mon and prod_tec):
            print("[WARN] Se requieren los datos iniciales de proveedores y productos previos.")
            return

        historiales_ejemplo = [
            # 1. TechSupply: Excelente desempeño (98% cumplimiento, 4 días, casi 0% defectos)
            {
                "proveedor_id": p_tech.id,
                "fecha_operacion": date(2026, 3, 15),
                "tiempo_entrega_promedio_dias": 4,
                "cumplimiento_porcentaje": Decimal("98.00"),
                "observaciones": "Entrega impecable de renovacion de equipos informaticos.",
                "detalles": [
                    {"producto_id": prod_lap.id, "solicitada": 50, "entregada": 50, "defectos": Decimal("0.0"), "obs": "Laptops en perfecto estado"},
                    {"producto_id": prod_mon.id, "solicitada": 50, "entregada": 50, "defectos": Decimal("0.5"), "obs": "1 monitor con pixel atascado, reemplazado de inmediato"},
                    {"producto_id": prod_tec.id, "solicitada": 50, "entregada": 50, "defectos": Decimal("0.0"), "obs": "Teclados completos"}
                ]
            },
            {
                "proveedor_id": p_tech.id,
                "fecha_operacion": date(2026, 6, 20),
                "tiempo_entrega_promedio_dias": 5,
                "cumplimiento_porcentaje": Decimal("96.50"),
                "observaciones": "Implementacion de servidores para datacenter secundario.",
                "detalles": [
                    {"producto_id": prod_srv.id, "solicitada": 2, "entregada": 2, "defectos": Decimal("0.0"), "obs": "Servidores configurados y testeados"},
                    {"producto_id": prod_lap.id, "solicitada": 20, "entregada": 20, "defectos": Decimal("0.0"), "obs": "Laptops para administradores"}
                ]
            },

            # 2. CompuGlobal: Desempeño medio (88% cumplimiento, 8 días, algunos defectos)
            {
                "proveedor_id": p_compu.id,
                "fecha_operacion": date(2026, 2, 10),
                "tiempo_entrega_promedio_dias": 8,
                "cumplimiento_porcentaje": Decimal("88.00"),
                "observaciones": "Compra masiva anual para sucursales del sur.",
                "detalles": [
                    {"producto_id": prod_lap.id, "solicitada": 80, "entregada": 78, "defectos": Decimal("2.5"), "obs": "Faltaron 2 unidades entregadas 3 dias despues"},
                    {"producto_id": prod_mon.id, "solicitada": 80, "entregada": 80, "defectos": Decimal("1.5"), "obs": "Empaques con leves abolladuras"},
                    {"producto_id": prod_mou.id, "solicitada": 80, "entregada": 80, "defectos": Decimal("1.0"), "obs": "Mouse funcionando"}
                ]
            },

            # 3. DigiTech: Buen equilibrio (92% cumplimiento, 5 días, 1% defectos)
            {
                "proveedor_id": p_digi.id,
                "fecha_operacion": date(2026, 4, 12),
                "tiempo_entrega_promedio_dias": 5,
                "cumplimiento_porcentaje": Decimal("93.00"),
                "observaciones": "Equipamiento de sala de capacitacion y oficina central.",
                "detalles": [
                    {"producto_id": prod_lap.id, "solicitada": 30, "entregada": 30, "defectos": Decimal("0.8"), "obs": "Excelente embalaje"},
                    {"producto_id": prod_mon.id, "solicitada": 30, "entregada": 30, "defectos": Decimal("1.0"), "obs": "Calidad visual alta"},
                    {"producto_id": prod_imp.id, "solicitada": 5, "entregada": 5, "defectos": Decimal("0.0"), "obs": "Impresoras funcionando con toners"}
                ]
            },

            # 4. LogiByte: Muy rápido en periféricos (95% cumplimiento, 3 días, 0.5% defectos)
            {
                "proveedor_id": p_logi.id,
                "fecha_operacion": date(2026, 5, 5),
                "tiempo_entrega_promedio_dias": 3,
                "cumplimiento_porcentaje": Decimal("95.00"),
                "observaciones": "Suministro urgente de accesorios y perifericos.",
                "detalles": [
                    {"producto_id": prod_tec.id, "solicitada": 100, "entregada": 100, "defectos": Decimal("0.5"), "obs": "Entrega antes del plazo pactado"},
                    {"producto_id": prod_mou.id, "solicitada": 100, "entregada": 100, "defectos": Decimal("0.0"), "obs": "Lotes completos"},
                    {"producto_id": prod_imp.id, "solicitada": 3, "entregada": 3, "defectos": Decimal("0.0"), "obs": "Equipos operativos"}
                ]
            }
        ]

        # Evitar duplicar si ya existen historiales
        conteo_actual = db.query(HistorialDesempeno).count()
        if conteo_actual == 0:
            for h_data in historiales_ejemplo:
                historial = HistorialDesempeno(
                    proveedor_id=h_data["proveedor_id"],
                    fecha_operacion=h_data["fecha_operacion"],
                    tiempo_entrega_promedio_dias=h_data["tiempo_entrega_promedio_dias"],
                    cumplimiento_porcentaje=h_data["cumplimiento_porcentaje"],
                    observaciones=h_data["observaciones"]
                )
                db.add(historial)
                db.flush()

                for det in h_data["detalles"]:
                    detalle = HistorialDesempenoDetalle(
                        historial_id=historial.id,
                        producto_id=det["producto_id"],
                        cantidad_solicitada=det["solicitada"],
                        cantidad_entregada=det["entregada"],
                        porcentaje_defectos=det["defectos"],
                        observaciones=det["obs"]
                    )
                    db.add(detalle)

            db.commit()
            print("[SUCCESS] Historiales de desempeno cargados exitosamente.")
        else:
            print(f"[INFO] Ya existen {conteo_actual} registros de historial en la base de datos.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al cargar historial: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_historial()
