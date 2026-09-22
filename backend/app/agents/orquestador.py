from typing import Dict, Any, List, Optional
from app.agents.financiero import AgenteFinanciero
from app.agents.calidad import AgenteCalidad
from app.agents.logistico import AgenteLogistico
from app.agents.riesgo import AgenteRiesgo
from app.agents.decisor import AgenteDecisor

class OrquestadorAgentes:
    """
    Orquestador Central de Agentes Inteligentes.
    Coordina el pipeline de análisis secuencial y emite el informe agéntico consolidado.
    """
    def __init__(self):
        self.financiero = AgenteFinanciero()
        self.calidad = AgenteCalidad()
        self.logistico = AgenteLogistico()
        self.riesgo = AgenteRiesgo()
        self.decisor = AgenteDecisor()

    def ejecutar_evaluacion_agentica(
        self,
        candidatos: List[Dict[str, Any]],
        metricas_historicas: Dict[int, Dict[str, Any]],
        prioridad: str,
        entrega_maxima_dias: Optional[int]
    ) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de agentes:
        1. Financiero + Calidad + Logístico (en paralelo o secuencial)
        2. Riesgo (consolida 1)
        3. Decisor (sintetiza y emite recomendación final)
        """
        if not candidatos:
            return {
                "estado": "Sin candidatos",
                "mensaje": "No se encontraron proveedores compatibles para orquestar.",
                "ranking": []
            }

        # Valores de referencia
        costos = [c["costo_total"] for c in candidatos if c["costo_total"] > 0]
        tiempos = [c["tiempo_entrega_max_dias"] for c in candidatos if c["tiempo_entrega_max_dias"] > 0]
        min_costo = min(costos) if costos else 1.0
        min_tiempo = min(tiempos) if tiempos else 1

        # Paso 1: Agentes de dominio especializado
        informe_financiero = self.financiero.analizar(candidatos, min_costo)
        informe_calidad = self.calidad.analizar(candidatos, metricas_historicas)
        informe_logistico = self.logistico.analizar(candidatos, min_tiempo, entrega_maxima_dias)

        # Paso 2: Agente de Riesgo
        informe_riesgo = self.riesgo.analizar(
            candidatos=candidatos,
            analisis_financiero=informe_financiero,
            analisis_calidad=informe_calidad,
            analisis_logistico=informe_logistico,
            metricas_por_proveedor=metricas_historicas
        )

        # Paso 3: Agente Decisor
        decision_final = self.decisor.decidir(
            candidatos=candidatos,
            analisis_financiero=informe_financiero,
            analisis_calidad=informe_calidad,
            analisis_logistico=informe_logistico,
            analisis_riesgo=informe_riesgo,
            prioridad=prioridad
        )

        return {
            "estado_orquestacion": "Completada",
            "agentes_participantes": [
                {"nombre": self.financiero.nombre, "rol": self.financiero.rol},
                {"nombre": self.calidad.nombre, "rol": self.calidad.rol},
                {"nombre": self.logistico.nombre, "rol": self.logistico.rol},
                {"nombre": self.riesgo.nombre, "rol": self.riesgo.rol},
                {"nombre": self.decisor.nombre, "rol": self.decisor.rol},
            ],
            "prioridad": prioridad,
            "ponderaciones": decision_final["ponderaciones"],
            "conclusion_ejecutiva": decision_final["conclusion_agente_decisor"],
            "proveedor_recomendado": decision_final["proveedor_recomendado"],
            "ranking": decision_final["ranking"],
            "detalles_agentes": {
                "financiero": informe_financiero,
                "calidad": informe_calidad,
                "logistico": informe_logistico,
                "riesgo": informe_riesgo
            }
        }
