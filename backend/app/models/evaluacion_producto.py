from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class EvaluacionProducto(Base):
    __tablename__ = "evaluacion_productos"

    id = Column(Integer, primary_key=True, index=True)
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    especificaciones = Column(Text, nullable=True)

    # Relaciones
    evaluacion = relationship("Evaluacion", back_populates="productos_solicitados")
    producto = relationship("Producto", back_populates="evaluaciones_producto")
