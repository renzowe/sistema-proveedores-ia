from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate

class ProductoService:
    @staticmethod
    def listar(db: Session, skip: int = 0, limit: int = 100, estado: Optional[str] = None) -> List[Producto]:
        query = db.query(Producto)
        if estado:
            query = query.filter(Producto.estado == estado)
        return query.order_by(Producto.id.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_id(db: Session, producto_id: int) -> Producto:
        producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado."
            )
        return producto

    @staticmethod
    def crear(db: Session, producto_in: ProductoCreate) -> Producto:
        nombre_limpio = producto_in.nombre.strip()
        if not nombre_limpio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre del producto no puede estar vacío."
            )

        if producto_in.codigo:
            codigo_limpio = producto_in.codigo.strip()
            existe = db.query(Producto).filter(Producto.codigo == codigo_limpio).first()
            if existe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un producto con el código {codigo_limpio}."
                )

        datos = producto_in.model_dump()
        datos["nombre"] = nombre_limpio
        if datos.get("codigo"):
            datos["codigo"] = datos["codigo"].strip()

        producto = Producto(**datos)
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto

    @staticmethod
    def actualizar(db: Session, producto_id: int, producto_in: ProductoUpdate) -> Producto:
        producto = ProductoService.obtener_por_id(db, producto_id)
        update_data = producto_in.model_dump(exclude_unset=True)

        if "nombre" in update_data and update_data["nombre"] is not None:
            nombre_limpio = update_data["nombre"].strip()
            if not nombre_limpio:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El nombre del producto no puede estar vacío."
                )
            update_data["nombre"] = nombre_limpio

        if "codigo" in update_data and update_data["codigo"]:
            codigo_limpio = update_data["codigo"].strip()
            if codigo_limpio != producto.codigo:
                existe = db.query(Producto).filter(Producto.codigo == codigo_limpio).first()
                if existe:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe un producto con el código {codigo_limpio}."
                    )
            update_data["codigo"] = codigo_limpio

        for key, value in update_data.items():
            setattr(producto, key, value)

        db.commit()
        db.refresh(producto)
        return producto

    @staticmethod
    def eliminar(db: Session, producto_id: int) -> None:
        producto = ProductoService.obtener_por_id(db, producto_id)
        db.delete(producto)
        db.commit()
