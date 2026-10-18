from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.fechas import ahora_utc

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    codigo = Column(String(50), unique=True, index=True, nullable=True)
    estado = Column(String(20), default="Activo")
    fecha_creacion = Column(DateTime, default=ahora_utc)

    # Relaciones
    proveedores_ofrecen = relationship("ProveedorProducto", back_populates="producto", cascade="all, delete-orphan")
    historiales_detalle = relationship("HistorialDesempenoDetalle", back_populates="producto", cascade="all, delete-orphan")
    evaluaciones_producto = relationship("EvaluacionProducto", back_populates="producto", cascade="all, delete-orphan")
