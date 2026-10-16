from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion_necesidad = Column(Text, nullable=True)
    fecha_evaluacion = Column(DateTime, default=datetime.utcnow)
    entrega_maxima_dias = Column(Integer, nullable=True)
    prioridad = Column(String(50), default="balanceado")
    estado = Column(String(50), default="Pendiente")

    # Relaciones
    productos_solicitados = relationship("EvaluacionProducto", back_populates="evaluacion", cascade="all, delete-orphan")
    detalles_resultado = relationship("EvaluacionDetalle", back_populates="evaluacion", cascade="all, delete-orphan")
