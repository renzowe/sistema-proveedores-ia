from sqlalchemy import Column, Integer, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class EvaluacionDetalle(Base):
    __tablename__ = "evaluacion_detalle"

    id = Column(Integer, primary_key=True, index=True)
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    puntaje_precio = Column(Numeric(5, 2), nullable=True)
    puntaje_calidad = Column(Numeric(5, 2), nullable=True)
    puntaje_logistica = Column(Numeric(5, 2), nullable=True)
    puntaje_historial = Column(Numeric(5, 2), nullable=True)
    puntaje_riesgo = Column(Numeric(5, 2), nullable=True)
    puntaje_final = Column(Numeric(5, 2), nullable=True)
    recomendado = Column(Boolean, default=False)
    explicacion = Column(Text, nullable=True)
    fecha_calculo = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    evaluacion = relationship("Evaluacion", back_populates="detalles_resultado")
    proveedor = relationship("Proveedor", back_populates="evaluaciones_detalle")
