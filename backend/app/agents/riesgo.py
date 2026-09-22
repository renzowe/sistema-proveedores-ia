from typing import Dict, Any, List
from app.utils.calculos import calcular_puntaje_riesgo, calcular_puntaje_historial

class AgenteRiesgo:
    """
    Agente Especializado en Mitigación y Gestión Integral de Riesgo.
    Consolida señales de cobertura de catálogo, antecedentes de cumplimiento y estabilidad del proveedor.
    """
    def __init__(self):
        self.nombre = "Agente de Riesgo"
        self.rol = "Gestión integral de riesgos operativos, contractuales y de cobertura"

    def analizar(
        self,
        candidatos: List[Dict[str, Any]],
        analisis_financiero: List[Dict[str, Any]],
        analisis_calidad: List[Dict[str, Any]],
        analisis_logistico: List[Dict[str, Any]],
        metricas_por_proveedor: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Mapear por ID para cruce
        fin_map = {f["proveedor_id"]: f for f in analisis_financiero}
        cal_map = {c["proveedor_id"]: c for c in analisis_calidad}
        log_map = {l["proveedor_id"]: l for l in analisis_logistico}

        resultados = []
        for cand in candidatos:
            prov_id = cand["proveedor_id"]
            metricas = metricas_por_proveedor.get(prov_id, {})
            cumplimiento = metricas.get("cumplimiento_promedio", 70.0)
            total_ops = metricas.get("total_operaciones", 0)
            cobertura_pct = cand["cobertura_porcentaje"]

            puntaje_historial = calcular_puntaje_historial(cumplimiento, total_ops)
            puntaje_riesgo = calcular_puntaje_riesgo(cobertura_pct, cumplimiento, total_ops)

            # Evaluar nivel de riesgo cualitativo
            factores_riesgo = []
            if cobertura_pct < 100:
                factores_riesgo.append(f"cobertura parcial ({cobertura_pct}%) que requiere compras complementarias")
            if not log_map.get(prov_id, {}).get("cumple_plazo_maximo", True):
                factores_riesgo.append("plazo ofertado excede el límite máximo requerido")
            if cal_map.get(prov_id, {}).get("tasa_defectos_promedio", 0.0) > 2.0:
                factores_riesgo.append("tasa de defectos histórica superior al umbral óptimo")
            if total_ops == 0:
                factores_riesgo.append("sin antecedentes operativos previos en el sistema")

            if puntaje_riesgo >= 85 and not factores_riesgo:
                dictamen = "DICTAMEN DE RIESGO BAJO: Proveedor con alta confiabilidad operativa, cobertura completa e historial sólido."
            elif puntaje_riesgo >= 70:
                dictamen = f"DICTAMEN DE RIESGO MODERADO: Nivel de riesgo aceptable con advertencias menores ({'; '.join(factores_riesgo)})."
            else:
                dictamen = f"DICTAMEN DE RIESGO ELEVADO: Se identificaron factores críticos de riesgo: {'; '.join(factores_riesgo)}. Se sugiere mitigar con garantías adicionales."

            resultados.append({
                "proveedor_id": prov_id,
                "razon_social": cand["razon_social"],
                "puntaje_historial": puntaje_historial,
                "puntaje_riesgo": puntaje_riesgo,
                "cumplimiento_historico_pct": cumplimiento,
                "total_operaciones_previas": total_ops,
                "nivel_riesgo": "Bajo" if puntaje_riesgo >= 85 else ("Moderado" if puntaje_riesgo >= 70 else "Alto"),
                "dictamen_riesgo": dictamen
            })
        return resultados
