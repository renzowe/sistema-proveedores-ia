from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String(255), nullable=False)
    ruc = Column(String(20), unique=True, index=True, nullable=False)
    nombre_comercial = Column(String(255), nullable=True)
    pais = Column(String(100), default="Perú")
    ciudad = Column(String(100), nullable=True)
    contacto = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    correo = Column(String(255), nullable=True)
    direccion = Column(Text, nullable=True)
    estado = Column(String(20), default="Activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    productos_ofrecidos = relationship("ProveedorProducto", back_populates="proveedor", cascade="all, delete-orphan")
    historiales = relationship("HistorialDesempeno", back_populates="proveedor", cascade="all, delete-orphan")
    evaluaciones_detalle = relationship("EvaluacionDetalle", back_populates="proveedor", cascade="all, delete-orphan")
