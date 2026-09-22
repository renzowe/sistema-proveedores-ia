from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status
from app.models.evaluacion import Evaluacion
from app.models.evaluacion_producto import EvaluacionProducto
from app.models.evaluacion_detalle import EvaluacionDetalle
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from app.models.proveedor_producto import ProveedorProducto
from app.schemas.evaluacion import EvaluacionCreate
from app.services.historial_service import HistorialService
from app.agents.orquestador import OrquestadorAgentes

class EvaluacionService:
    @staticmethod
    def listar(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[str] = None
    ) -> List[Evaluacion]:
        query = db.query(Evaluacion)
        if estado:
            query = query.filter(Evaluacion.estado == estado)
        return query.order_by(Evaluacion.fecha_evaluacion.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_id(db: Session, evaluacion_id: int) -> Evaluacion:
        evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
        if not evaluacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluación con ID {evaluacion_id} no encontrada."
            )
        return evaluacion

    @staticmethod
    def crear(db: Session, evaluacion_in: EvaluacionCreate) -> Evaluacion:
        if not evaluacion_in.productos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe incluir al menos un producto a evaluar."
            )

        if not evaluacion_in.titulo or not evaluacion_in.titulo.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El título de la evaluación es obligatorio."
            )

        for prod_in in evaluacion_in.productos:
            prod = db.query(Producto).filter(Producto.id == prod_in.producto_id).first()
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con ID {prod_in.producto_id} no existe."
                )
            if prod_in.cantidad <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La cantidad para el producto {prod.nombre} debe ser mayor a 0."
                )

        eval_data = evaluacion_in.model_dump(exclude={"productos"})
        eval_data["titulo"] = eval_data["titulo"].strip()
        
        evaluacion = Evaluacion(**eval_data)
        db.add(evaluacion)
        db.flush()

        for prod_in in evaluacion_in.productos:
            eval_prod = EvaluacionProducto(
                evaluacion_id=evaluacion.id,
                **prod_in.model_dump()
            )
            db.add(eval_prod)

        db.commit()
        db.refresh(evaluacion)
        return evaluacion

    @staticmethod
    def buscar_proveedores_compatibles(db: Session, evaluacion_id: int) -> Dict[str, Any]:
        evaluacion = EvaluacionService.obtener_por_id(db, evaluacion_id)
        productos_requeridos = evaluacion.productos_solicitados
        total_requeridos = len(productos_requeridos)

        if total_requeridos == 0:
            return {
                "evaluacion_id": evaluacion.id,
                "titulo": evaluacion.titulo,
                "total_productos_solicitados": 0,
                "proveedores_compatibles": []
            }

        req_dict = {p.producto_id: p for p in productos_requeridos}
        prod_ids_requeridos = list(req_dict.keys())

        ofertas = db.query(ProveedorProducto).filter(
            ProveedorProducto.producto_id.in_(prod_ids_requeridos),
            ProveedorProducto.disponible == True
        ).all()

        proveedores_map: Dict[int, Dict[str, Any]] = {}

        for oferta in ofertas:
            prov = oferta.proveedor
            if not prov or prov.estado != "Activo":
                continue

            if prov.id not in proveedores_map:
                proveedores_map[prov.id] = {
                    "proveedor_id": prov.id,
                    "razon_social": prov.razon_social,
                    "ruc": prov.ruc,
                    "contacto": prov.contacto,
                    "telefono": prov.telefono,
                    "correo": prov.correo,
                    "ciudad": prov.ciudad,
                    "productos_ofrecidos": [],
                    "productos_faltantes": []
                }

            req_item = req_dict[oferta.producto_id]
            precio_unitario = float(oferta.precio)
            cantidad = req_item.cantidad
            subtotal = round(precio_unitario * cantidad, 2)

            proveedores_map[prov.id]["productos_ofrecidos"].append({
                "producto_id": oferta.producto_id,
                "nombre_producto": oferta.producto.nombre if oferta.producto else "",
                "codigo_producto": oferta.producto.codigo if oferta.producto else "",
                "cantidad_solicitada": cantidad,
                "precio_unitario": precio_unitario,
                "tiempo_entrega_dias": oferta.tiempo_entrega_dias,
                "subtotal": subtotal,
                "condiciones": oferta.condiciones
            })

        lista_proveedores = []
        for prov_id, prov_data in proveedores_map.items():
            ofrecidos_ids = {p["producto_id"] for p in prov_data["productos_ofrecidos"]}
            
            for prod_id, req_item in req_dict.items():
                if prod_id not in ofrecidos_ids:
                    prod_obj = req_item.producto
                    prov_data["productos_faltantes"].append({
                        "producto_id": prod_id,
                        "nombre_producto": prod_obj.nombre if prod_obj else "",
                        "cantidad_solicitada": req_item.cantidad
                    })

            cant_ofrecidos = len(prov_data["productos_ofrecidos"])
            cobertura_pct = round((cant_ofrecidos / total_requeridos) * 100, 2)
            costo_total = round(sum(p["subtotal"] for p in prov_data["productos_ofrecidos"]), 2)
            tiempo_max_dias = max(p["tiempo_entrega_dias"] for p in prov_data["productos_ofrecidos"]) if prov_data["productos_ofrecidos"] else 0

            cumple_plazo = True
            if evaluacion.entrega_maxima_dias is not None and evaluacion.entrega_maxima_dias > 0:
                cumple_plazo = tiempo_max_dias <= evaluacion.entrega_maxima_dias

            prov_data["total_ofrecidos"] = cant_ofrecidos
            prov_data["total_solicitados"] = total_requeridos
            prov_data["cobertura_porcentaje"] = cobertura_pct
            prov_data["es_cobertura_total"] = (cant_ofrecidos == total_requeridos)
            prov_data["costo_total"] = costo_total
            prov_data["tiempo_entrega_max_dias"] = tiempo_max_dias
            prov_data["cumple_plazo_maximo"] = cumple_plazo

            lista_proveedores.append(prov_data)

        lista_proveedores.sort(key=lambda x: (-x["cobertura_porcentaje"], x["costo_total"]))

        return {
            "evaluacion_id": evaluacion.id,
            "titulo": evaluacion.titulo,
            "prioridad": evaluacion.prioridad,
            "entrega_maxima_dias": evaluacion.entrega_maxima_dias,
            "total_productos_solicitados": total_requeridos,
            "total_proveedores_compatibles": len(lista_proveedores),
            "proveedores_compatibles": lista_proveedores
        }

    @staticmethod
    def ejecutar_evaluacion(db: Session, evaluacion_id: int) -> Dict[str, Any]:
        """
        Ejecuta la evaluación mediante la arquitectura de agentes inteligentes:
        Orquestador -> [Financiero, Calidad, Logístico] -> Riesgo -> Decisor.
        """
        evaluacion = EvaluacionService.obtener_por_id(db, evaluacion_id)
        compatibilidad = EvaluacionService.buscar_proveedores_compatibles(db, evaluacion_id)
        candidatos = compatibilidad["proveedores_compatibles"]

        if not candidatos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No existen proveedores compatibles con el catálogo de productos solicitado."
            )

        # Recolectar métricas de historial por proveedor
        metricas_historicas = {}
        for cand in candidatos:
            prov_id = cand["proveedor_id"]
            metricas_historicas[prov_id] = HistorialService.obtener_metricas_proveedor(db, prov_id)

        # Invocar al Orquestador Agéntico
        orquestador = OrquestadorAgentes()
        resultado_agentes = orquestador.ejecutar_evaluacion_agentica(
            candidatos=candidatos,
            metricas_historicas=metricas_historicas,
            prioridad=evaluacion.prioridad,
            entrega_maxima_dias=evaluacion.entrega_maxima_dias
        )

        ranking = resultado_agentes["ranking"]

        # Persistir resultados en evaluacion_detalle
        db.query(EvaluacionDetalle).filter(EvaluacionDetalle.evaluacion_id == evaluacion.id).delete()

        for r in ranking:
            detalle_db = EvaluacionDetalle(
                evaluacion_id=evaluacion.id,
                proveedor_id=r["proveedor_id"],
                puntaje_precio=Decimal(str(r["puntajes"]["precio"])),
                puntaje_calidad=Decimal(str(r["puntajes"]["calidad"])),
                puntaje_logistica=Decimal(str(r["puntajes"]["logistica"])),
                puntaje_historial=Decimal(str(r["puntajes"]["historial"])),
                puntaje_riesgo=Decimal(str(r["puntajes"]["riesgo"])),
                puntaje_final=Decimal(str(r["puntajes"]["final"])),
                recomendado=r["recomendado"],
                explicacion=r["explicacion"],
                fecha_calculo=datetime.utcnow()
            )
            db.add(detalle_db)

        evaluacion.estado = "Procesada"
        db.commit()
        db.refresh(evaluacion)

        return {
            "evaluacion_id": evaluacion.id,
            "titulo": evaluacion.titulo,
            "prioridad_aplicada": evaluacion.prioridad,
            "ponderaciones": resultado_agentes["ponderaciones"],
            "estado": evaluacion.estado,
            "conclusion_ejecutiva": resultado_agentes["conclusion_ejecutiva"],
            "proveedor_recomendado": resultado_agentes["proveedor_recomendado"],
            "ranking": ranking
        }

    @staticmethod
    def obtener_informe_agentes(db: Session, evaluacion_id: int) -> Dict[str, Any]:
        """
        Genera el informe agéntico detallado con las opiniones de cada agente especializado.
        """
        evaluacion = EvaluacionService.obtener_por_id(db, evaluacion_id)
        compatibilidad = EvaluacionService.buscar_proveedores_compatibles(db, evaluacion_id)
        candidatos = compatibilidad["proveedores_compatibles"]

        if not candidatos:
            return {
                "evaluacion_id": evaluacion.id,
                "titulo": evaluacion.titulo,
                "mensaje": "Sin proveedores compatibles.",
                "detalles_agentes": {}
            }

        metricas_historicas = {}
        for cand in candidatos:
            prov_id = cand["proveedor_id"]
            metricas_historicas[prov_id] = HistorialService.obtener_metricas_proveedor(db, prov_id)

        orquestador = OrquestadorAgentes()
        return orquestador.ejecutar_evaluacion_agentica(
            candidatos=candidatos,
            metricas_historicas=metricas_historicas,
            prioridad=evaluacion.prioridad,
            entrega_maxima_dias=evaluacion.entrega_maxima_dias
        )

    @staticmethod
    def obtener_resultados(db: Session, evaluacion_id: int) -> Dict[str, Any]:
        evaluacion = EvaluacionService.obtener_por_id(db, evaluacion_id)
        detalles = db.query(EvaluacionDetalle).filter(
            EvaluacionDetalle.evaluacion_id == evaluacion_id
        ).order_by(EvaluacionDetalle.puntaje_final.desc()).all()

        if not detalles:
            return {
                "evaluacion_id": evaluacion.id,
                "titulo": evaluacion.titulo,
                "estado": evaluacion.estado,
                "mensaje": "Esta evaluación aún no ha sido procesada.",
                "resultados": []
            }

        resultados = []
        for d in detalles:
            resultados.append({
                "id": d.id,
                "proveedor_id": d.proveedor_id,
                "proveedor_nombre": d.proveedor.razon_social if d.proveedor else None,
                "proveedor_ruc": d.proveedor.ruc if d.proveedor else None,
                "puntaje_precio": float(d.puntaje_precio),
                "puntaje_calidad": float(d.puntaje_calidad),
                "puntaje_logistica": float(d.puntaje_logistica),
                "puntaje_historial": float(d.puntaje_historial),
                "puntaje_riesgo": float(d.puntaje_riesgo),
                "puntaje_final": float(d.puntaje_final),
                "recomendado": d.recomendado,
                "explicacion": d.explicacion,
                "fecha_calculo": d.fecha_calculo
            })

        return {
            "evaluacion_id": evaluacion.id,
            "titulo": evaluacion.titulo,
            "prioridad": evaluacion.prioridad,
            "estado": evaluacion.estado,
            "proveedor_recomendado": next((r for r in resultados if r["recomendado"]), None),
            "ranking": resultados
        }

    @staticmethod
    def eliminar(db: Session, evaluacion_id: int) -> None:
        evaluacion = EvaluacionService.obtener_por_id(db, evaluacion_id)
        db.delete(evaluacion)
        db.commit()
