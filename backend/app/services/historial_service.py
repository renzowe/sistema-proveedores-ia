from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import HTTPException, status
from app.models.historial_desempeno import HistorialDesempeno
from app.models.historial_desempeno_detalle import HistorialDesempenoDetalle
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.schemas.historial_desempeno import HistorialDesempenoCreate

class HistorialService:
    @staticmethod
    def listar(
        db: Session,
        proveedor_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialDesempeno]:
        query = db.query(HistorialDesempeno)
        if proveedor_id:
            query = query.filter(HistorialDesempeno.proveedor_id == proveedor_id)
        return query.order_by(HistorialDesempeno.fecha_operacion.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_id(db: Session, id: int) -> HistorialDesempeno:
        historial = db.query(HistorialDesempeno).filter(HistorialDesempeno.id == id).first()
        if not historial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro de historial con ID {id} no encontrado."
            )
        return historial

    @staticmethod
    def registrar(db: Session, historial_in: HistorialDesempenoCreate) -> HistorialDesempeno:
        # 1. Validar que el proveedor exista
        proveedor = db.query(Proveedor).filter(Proveedor.id == historial_in.proveedor_id).first()
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {historial_in.proveedor_id} no existe."
            )

        # 2. Validar que los productos en el detalle existan y tengan cantidades coherentes
        if not historial_in.detalles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe incluir al menos un producto en el detalle del historial."
            )

        for det in historial_in.detalles:
            prod = db.query(Producto).filter(Producto.id == det.producto_id).first()
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con ID {det.producto_id} no existe."
                )
            if det.cantidad_solicitada <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La cantidad solicitada para el producto {prod.nombre} debe ser mayor a 0."
                )
            if det.cantidad_entregada < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La cantidad entregada para el producto {prod.nombre} no puede ser negativa."
                )
            if det.porcentaje_defectos < 0 or det.porcentaje_defectos > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El porcentaje de defectos para {prod.nombre} debe estar entre 0 y 100."
                )

        # 3. Crear cabecera
        historial_data = historial_in.model_dump(exclude={"detalles"})
        historial = HistorialDesempeno(**historial_data)
        db.add(historial)
        db.flush()

        # 4. Crear detalles
        for det_in in historial_in.detalles:
            detalle = HistorialDesempenoDetalle(
                historial_id=historial.id,
                **det_in.model_dump()
            )
            db.add(detalle)

        db.commit()
        db.refresh(historial)
        return historial

    @staticmethod
    def obtener_metricas_proveedor(db: Session, proveedor_id: int) -> Dict[str, Any]:
        # Validar proveedor
        proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {proveedor_id} no existe."
            )

        historiales = db.query(HistorialDesempeno).filter(
            HistorialDesempeno.proveedor_id == proveedor_id
        ).all()

        if not historiales:
            return {
                "proveedor_id": proveedor_id,
                "razon_social": proveedor.razon_social,
                "total_operaciones": 0,
                "cumplimiento_promedio": 0.0,
                "tiempo_entrega_promedio_dias": 0.0,
                "tasa_defectos_promedio": 0.0,
                "total_solicitado": 0,
                "total_entregado": 0,
                "tasa_efectividad_entrega": 0.0
            }

        total_ops = len(historiales)
        cumplimiento_valores = [float(h.cumplimiento_porcentaje) for h in historiales if h.cumplimiento_porcentaje is not None]
        tiempos_valores = [h.tiempo_entrega_promedio_dias for h in historiales if h.tiempo_entrega_promedio_dias is not None]

        cumplimiento_prom = sum(cumplimiento_valores) / len(cumplimiento_valores) if cumplimiento_valores else 0.0
        tiempo_prom = sum(tiempos_valores) / len(tiempos_valores) if tiempos_valores else 0.0

        # Métricas desde los detalles de productos
        historial_ids = [h.id for h in historiales]
        detalles = db.query(HistorialDesempenoDetalle).filter(
            HistorialDesempenoDetalle.historial_id.in_(historial_ids)
        ).all()

        total_solicitado = sum(d.cantidad_solicitada for d in detalles)
        total_entregado = sum(d.cantidad_entregada for d in detalles)
        defectos_valores = [float(d.porcentaje_defectos) for d in detalles if d.porcentaje_defectos is not None]
        defectos_prom = sum(defectos_valores) / len(defectos_valores) if defectos_valores else 0.0

        efectividad_entrega = (total_entregado / total_solicitado * 100) if total_solicitado > 0 else 0.0

        return {
            "proveedor_id": proveedor_id,
            "razon_social": proveedor.razon_social,
            "total_operaciones": total_ops,
            "cumplimiento_promedio": round(cumplimiento_prom, 2),
            "tiempo_entrega_promedio_dias": round(tiempo_prom, 2),
            "tasa_defectos_promedio": round(defectos_prom, 2),
            "total_solicitado": total_solicitado,
            "total_entregado": total_entregado,
            "tasa_efectividad_entrega": round(efectividad_entrega, 2)
        }

    @staticmethod
    def obtener_historial_por_producto(db: Session, producto_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        # Validar producto
        producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no existe."
            )

        detalles = db.query(HistorialDesempenoDetalle).join(HistorialDesempeno).filter(
            HistorialDesempenoDetalle.producto_id == producto_id
        ).offset(skip).limit(limit).all()

        resultado = []
        for d in detalles:
            h = d.historial
            resultado.append({
                "historial_id": h.id,
                "proveedor_id": h.proveedor_id,
                "proveedor_nombre": h.proveedor.razon_social if h.proveedor else None,
                "fecha_operacion": h.fecha_operacion,
                "cantidad_solicitada": d.cantidad_solicitada,
                "cantidad_entregada": d.cantidad_entregada,
                "porcentaje_defectos": float(d.porcentaje_defectos),
                "cumplimiento_porcentaje": float(h.cumplimiento_porcentaje) if h.cumplimiento_porcentaje else None,
                "tiempo_entrega_dias": h.tiempo_entrega_promedio_dias,
                "observaciones": d.observaciones
            })
        return resultado

    @staticmethod
    def eliminar(db: Session, id: int) -> None:
        historial = HistorialService.obtener_por_id(db, id)
        db.delete(historial)
        db.commit()
