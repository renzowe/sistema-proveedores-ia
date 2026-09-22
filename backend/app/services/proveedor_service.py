from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.proveedor import Proveedor
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate
from app.utils.validaciones import validar_ruc, validar_email, validar_telefono

class ProveedorService:
    @staticmethod
    def listar(db: Session, skip: int = 0, limit: int = 100, estado: Optional[str] = None) -> List[Proveedor]:
        query = db.query(Proveedor)
        if estado:
            query = query.filter(Proveedor.estado == estado)
        return query.order_by(Proveedor.id.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def obtener_por_id(db: Session, proveedor_id: int) -> Proveedor:
        proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {proveedor_id} no encontrado."
            )
        return proveedor

    @staticmethod
    def crear(db: Session, proveedor_in: ProveedorCreate) -> Proveedor:
        validar_ruc(proveedor_in.ruc)
        if proveedor_in.correo:
            validar_email(proveedor_in.correo)
        if proveedor_in.telefono:
            validar_telefono(proveedor_in.telefono)

        existe = db.query(Proveedor).filter(Proveedor.ruc == proveedor_in.ruc.strip()).first()
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un proveedor registrado con el RUC {proveedor_in.ruc}."
            )

        datos = proveedor_in.model_dump()
        datos["ruc"] = datos["ruc"].strip()
        if datos.get("correo"):
            datos["correo"] = datos["correo"].strip()
        if datos.get("telefono"):
            datos["telefono"] = datos["telefono"].strip()

        proveedor = Proveedor(**datos)
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        return proveedor

    @staticmethod
    def actualizar(db: Session, proveedor_id: int, proveedor_in: ProveedorUpdate) -> Proveedor:
        proveedor = ProveedorService.obtener_por_id(db, proveedor_id)
        update_data = proveedor_in.model_dump(exclude_unset=True)

        if "ruc" in update_data and update_data["ruc"]:
            validar_ruc(update_data["ruc"])
            ruc_limpio = update_data["ruc"].strip()
            if ruc_limpio != proveedor.ruc:
                existe = db.query(Proveedor).filter(Proveedor.ruc == ruc_limpio).first()
                if existe:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe otro proveedor con el RUC {ruc_limpio}."
                    )
            update_data["ruc"] = ruc_limpio

        if "correo" in update_data and update_data["correo"]:
            validar_email(update_data["correo"])
            update_data["correo"] = update_data["correo"].strip()

        if "telefono" in update_data and update_data["telefono"]:
            validar_telefono(update_data["telefono"])
            update_data["telefono"] = update_data["telefono"].strip()

        for key, value in update_data.items():
            setattr(proveedor, key, value)

        db.commit()
        db.refresh(proveedor)
        return proveedor

    @staticmethod
    def eliminar(db: Session, proveedor_id: int) -> None:
        proveedor = ProveedorService.obtener_por_id(db, proveedor_id)
        db.delete(proveedor)
        db.commit()
