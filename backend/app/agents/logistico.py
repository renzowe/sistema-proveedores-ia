from typing import Dict, Any, List, Optional
from app.utils.calculos import calcular_puntaje_logistica

class AgenteLogistico:
    """
    Agente Especializado en Cadena de Suministro y Logística.
    Evalúa tiempos de entrega ofertados, cumplimiento de fechas límite y puntualidad histórica.
    """
    def __init__(self):
        self.nombre = "Agente Logístico"
        self.rol = "Evaluación de tiempos de entrega, capacidad de despacho y puntualidad"

    def analizar(
        self,
        candidatos: List[Dict[str, Any]],
        min_tiempo_global: int,
        entrega_maxima_dias: Optional[int]
    ) -> List[Dict[str, Any]]:
        resultados = []
        for cand in candidatos:
            tiempo_dias = cand["tiempo_entrega_max_dias"]
            cumple_plazo = cand["cumple_plazo_maximo"]
            
            puntaje_logistica = calcular_puntaje_logistica(
                tiempo_proveedor_dias=tiempo_dias,
                tiempo_minimo_todos_dias=min_tiempo_global,
                entrega_maxima_dias=entrega_maxima_dias
            )

            if entrega_maxima_dias and not cumple_plazo:
                dictamen = f"DICTAMEN LOGÍSTICO DESFAVORABLE: Plazo ofertado ({tiempo_dias} días) supera el límite requerido ({entrega_maxima_dias} días). Riesgo de demora operativa."
            elif tiempo_dias == min_tiempo_global:
                dictamen = f"DICTAMEN LOGÍSTICO DESTACADO: Plazo de entrega más rápido del grupo ({tiempo_dias} días). Capacidad de respuesta inmediata."
            else:
                dictamen = f"DICTAMEN LOGÍSTICO CONFORME: Plazo de entrega de {tiempo_dias} días dentro de los parámetros aceptables de despacho."

            resultados.append({
                "proveedor_id": cand["proveedor_id"],
                "razon_social": cand["razon_social"],
                "puntaje_logistica": puntaje_logistica,
                "tiempo_entrega_max_dias": tiempo_dias,
                "cumple_plazo_maximo": cumple_plazo,
                "dictamen_logistico": dictamen
            })
        return resultados
