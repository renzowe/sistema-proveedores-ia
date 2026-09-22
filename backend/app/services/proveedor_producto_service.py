from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.proveedor_producto import ProveedorProducto
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.schemas.proveedor_producto import ProveedorProductoCreate, ProveedorProductoUpdate

class ProveedorProductoService:
    @staticmethod
    def listar(
        db: Session,
        proveedor_id: Optional[int] = None,
        producto_id: Optional[int] = None,
        disponible_solo: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProveedorProducto]:
        query = db.query(ProveedorProducto)
        if proveedor_id:
            query = query.filter(ProveedorProducto.proveedor_id == proveedor_id)
        if producto_id:
            query = query.filter(ProveedorProducto.producto_id == producto_id)
        if disponible_solo:
            query = query.filter(ProveedorProducto.disponible == True)
        return query.order_by(ProveedorProducto.id.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_id(db: Session, id: int) -> ProveedorProducto:
        relacion = db.query(ProveedorProducto).filter(ProveedorProducto.id == id).first()
        if not relacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relación proveedor-producto con ID {id} no encontrada."
            )
        return relacion

    @staticmethod
    def asignar(db: Session, relacion_in: ProveedorProductoCreate) -> ProveedorProducto:
        # Validar existencia del proveedor
        proveedor = db.query(Proveedor).filter(Proveedor.id == relacion_in.proveedor_id).first()
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {relacion_in.proveedor_id} no existe."
            )

        # Validar existencia del producto
        producto = db.query(Producto).filter(Producto.id == relacion_in.producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {relacion_in.producto_id} no existe."
            )

        # Validar que precio y tiempo sean válidos
        if relacion_in.precio <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio unitario debe ser mayor a 0."
            )
        if relacion_in.tiempo_entrega_dias <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tiempo de entrega debe ser al menos 1 día."
            )

        # Validar unicidad de la relación
        existe = db.query(ProveedorProducto).filter(
            ProveedorProducto.proveedor_id == relacion_in.proveedor_id,
            ProveedorProducto.producto_id == relacion_in.producto_id
        ).first()
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proveedor ya tiene asignado este producto en su catálogo."
            )

        relacion = ProveedorProducto(**relacion_in.model_dump())
        db.add(relacion)
        db.commit()
        db.refresh(relacion)
        return relacion

    @staticmethod
    def actualizar(db: Session, id: int, relacion_in: ProveedorProductoUpdate) -> ProveedorProducto:
        relacion = ProveedorProductoService.obtener_por_id(db, id)
        update_data = relacion_in.model_dump(exclude_unset=True)

        if "precio" in update_data and update_data["precio"] is not None:
            if update_data["precio"] <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El precio unitario debe ser mayor a 0."
                )

        if "tiempo_entrega_dias" in update_data and update_data["tiempo_entrega_dias"] is not None:
            if update_data["tiempo_entrega_dias"] <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El tiempo de entrega debe ser al menos 1 día."
                )

        for key, value in update_data.items():
            setattr(relacion, key, value)

        db.commit()
        db.refresh(relacion)
        return relacion

    @staticmethod
    def eliminar(db: Session, id: int) -> None:
        relacion = ProveedorProductoService.obtener_por_id(db, id)
        db.delete(relacion)
        db.commit()
