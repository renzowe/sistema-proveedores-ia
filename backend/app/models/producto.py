from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    codigo = Column(String(50), unique=True, index=True, nullable=True)
    estado = Column(String(20), default="Activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    proveedores_ofrecen = relationship("ProveedorProducto", back_populates="producto", cascade="all, delete-orphan")
    historiales_detalle = relationship("HistorialDesempenoDetalle", back_populates="producto", cascade="all, delete-orphan")
    evaluaciones_producto = relationship("EvaluacionProducto", back_populates="producto", cascade="all, delete-orphan")
