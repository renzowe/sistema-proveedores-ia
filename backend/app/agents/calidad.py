from typing import Dict, Any, List
from app.utils.calculos import calcular_puntaje_calidad

class AgenteCalidad:
    """
    Agente Especializado en Control y Aseguramiento de la Calidad.
    Evalúa tasas históricas de defectos, condiciones de garantía y confiabilidad de productos.
    """
    def __init__(self):
        self.nombre = "Agente de Calidad"
        self.rol = "Evaluación de estándares técnicos, garantía y control de defectos"

    def analizar(
        self,
        candidatos: List[Dict[str, Any]],
        metricas_por_proveedor: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        resultados = []
        for cand in candidatos:
            prov_id = cand["proveedor_id"]
            metricas = metricas_por_proveedor.get(prov_id, {})
            tasa_defectos = metricas.get("tasa_defectos_promedio", 0.0)
            
            puntaje_calidad = calcular_puntaje_calidad(tasa_defectos)

            if tasa_defectos == 0.0 and metricas.get("total_operaciones", 0) > 0:
                dictamen = f"DICTAMEN DE CALIDAD EXCELENTE: Tasa de defectos del 0.00% con historial comprobado. Cumple con los más altos estándares de calidad."
            elif tasa_defectos <= 1.0:
                dictamen = f"DICTAMEN DE CALIDAD ÓPTIMO: Tasa de defectos baja ({tasa_defectos:.2f}%). Productos con altos estándares de fiabilidad."
            elif tasa_defectos <= 3.0:
                dictamen = f"DICTAMEN DE CALIDAD ACEPTABLE: Tasa de defectos moderada ({tasa_defectos:.2f}%). Se recomienda exigir cláusulas estrictas de cambio en garantía."
            else:
                dictamen = f"DICTAMEN DE CALIDAD EN ALERTA: Tasa de defectos elevada ({tasa_defectos:.2f}%). Representa riesgo de reclamos o devoluciones."

            resultados.append({
                "proveedor_id": prov_id,
                "razon_social": cand["razon_social"],
                "puntaje_calidad": puntaje_calidad,
                "tasa_defectos_promedio": tasa_defectos,
                "dictamen_calidad": dictamen
            })
        return resultados
