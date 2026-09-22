from sqlalchemy import Column, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class HistorialDesempenoDetalle(Base):
    __tablename__ = "historial_desempeno_detalle"

    id = Column(Integer, primary_key=True, index=True)
    historial_id = Column(Integer, ForeignKey("historial_desempeno.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    cantidad_solicitada = Column(Integer, nullable=False, default=0)
    cantidad_entregada = Column(Integer, nullable=False, default=0)
    porcentaje_defectos = Column(Numeric(5, 2), default=0.0)
    observaciones = Column(Text, nullable=True)

    # Relaciones
    historial = relationship("HistorialDesempeno", back_populates="detalles")
    producto = relationship("Producto", back_populates="historiales_detalle")
