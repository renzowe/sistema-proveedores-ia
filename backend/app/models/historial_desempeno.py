from sqlalchemy import Column, Integer, Numeric, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class HistorialDesempeno(Base):
    __tablename__ = "historial_desempeno"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    fecha_operacion = Column(Date, nullable=False)
    tiempo_entrega_promedio_dias = Column(Integer, nullable=True)
    cumplimiento_porcentaje = Column(Numeric(5, 2), nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    proveedor = relationship("Proveedor", back_populates="historiales")
    detalles = relationship("HistorialDesempenoDetalle", back_populates="historial", cascade="all, delete-orphan")
