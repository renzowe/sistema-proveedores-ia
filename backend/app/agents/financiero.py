from typing import Dict, Any, List
from app.utils.calculos import calcular_puntaje_precio

class AgenteFinanciero:
    """
    Agente Especializado en Análisis Financiero y Estructura de Costos.
    Evalúa la competitividad de precios, costo total de la canasta y ahorro estimado.
    """
    def __init__(self):
        self.nombre = "Agente Financiero"
        self.rol = "Evaluación de costos, precios unitarios y optimización presupuestal"

    def analizar(
        self,
        candidatos: List[Dict[str, Any]],
        min_costo_global: float
    ) -> List[Dict[str, Any]]:
        resultados = []
        for cand in candidatos:
            costo_total = cand["costo_total"]
            puntaje_precio = calcular_puntaje_precio(costo_total, min_costo_global)
            
            diferencia_min = round(costo_total - min_costo_global, 2)
            es_mas_economico = (diferencia_min == 0)

            if es_mas_economico:
                dictamen = f"DICTAMEN FINANCIERO FAVORABLE: Ofrece la propuesta más económica con un costo total de S/ {costo_total:,.2f}."
            elif puntaje_precio >= 85:
                dictamen = f"DICTAMEN FINANCIERO COMPETITIVO: Costo total de S/ {costo_total:,.2f} (+S/ {diferencia_min:,.2f} respecto al mínimo). Buena relación costo-beneficio."
            else:
                dictamen = f"DICTAMEN FINANCIERO OBSERVADO: Costo total de S/ {costo_total:,.2f} (+S/ {diferencia_min:,.2f} sobre la opción más económica). Requiere negociación de tarifas."

            resultados.append({
                "proveedor_id": cand["proveedor_id"],
                "razon_social": cand["razon_social"],
                "puntaje_precio": puntaje_precio,
                "costo_total": costo_total,
                "diferencia_respecto_minimo": diferencia_min,
                "es_mas_economico": es_mas_economico,
                "dictamen_financiero": dictamen
            })
        return resultados
