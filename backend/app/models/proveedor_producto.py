from sqlalchemy import Column, Integer, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ProveedorProducto(Base):
    __tablename__ = "proveedor_productos"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    tiempo_entrega_dias = Column(Integer, nullable=False, default=1)
    condiciones = Column(Text, nullable=True)
    disponible = Column(Boolean, default=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proveedor = relationship("Proveedor", back_populates="productos_ofrecidos")
    producto = relationship("Producto", back_populates="proveedores_ofrecen")
