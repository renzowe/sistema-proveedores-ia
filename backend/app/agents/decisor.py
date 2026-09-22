from typing import Dict, Any, List
from app.utils.calculos import calcular_puntaje_final, obtener_ponderaciones, generar_explicacion_resultado

class AgenteDecisor:
    """
    Agente Especializado en Toma de Decisiones y Recomendación Final.
    Integra los dictámenes de Financiero, Calidad, Logístico y Riesgo, pondera los criterios y emite el veredicto final.
    """
    def __init__(self):
        self.nombre = "Agente Decisor"
        self.rol = "Síntesis multicriterio, ponderación y recomendación final ejecutiva"

    def decidir(
        self,
        candidatos: List[Dict[str, Any]],
        analisis_financiero: List[Dict[str, Any]],
        analisis_calidad: List[Dict[str, Any]],
        analisis_logistico: List[Dict[str, Any]],
        analisis_riesgo: List[Dict[str, Any]],
        prioridad: str
    ) -> Dict[str, Any]:
        ponderaciones = obtener_ponderaciones(prioridad)

        fin_map = {f["proveedor_id"]: f for f in analisis_financiero}
        cal_map = {c["proveedor_id"]: c for c in analisis_calidad}
        log_map = {l["proveedor_id"]: l for l in analisis_logistico}
        rie_map = {r["proveedor_id"]: r for r in analisis_riesgo}

        ranking = []
        for cand in candidatos:
            prov_id = cand["proveedor_id"]
            p_precio = fin_map[prov_id]["puntaje_precio"]
            p_calidad = cal_map[prov_id]["puntaje_calidad"]
            p_logistica = log_map[prov_id]["puntaje_logistica"]
            p_historial = rie_map[prov_id]["puntaje_historial"]
            p_riesgo = rie_map[prov_id]["puntaje_riesgo"]

            puntajes = {
                "precio": p_precio,
                "calidad": p_calidad,
                "logistica": p_logistica,
                "historial": p_historial,
                "riesgo": p_riesgo
            }
            p_final = calcular_puntaje_final(puntajes, ponderaciones)
            puntajes["final"] = p_final

            ranking.append({
                "proveedor_id": prov_id,
                "razon_social": cand["razon_social"],
                "ruc": cand["ruc"],
                "costo_total": cand["costo_total"],
                "tiempo_entrega_max_dias": cand["tiempo_entrega_max_dias"],
                "cobertura_porcentaje": cand["cobertura_porcentaje"],
                "cumplimiento_promedio": rie_map[prov_id]["cumplimiento_historico_pct"],
                "puntajes": puntajes,
                "recomendado": False,
                "dictamenes": {
                    "financiero": fin_map[prov_id]["dictamen_financiero"],
                    "calidad": cal_map[prov_id]["dictamen_calidad"],
                    "logistico": log_map[prov_id]["dictamen_logistico"],
                    "riesgo": rie_map[prov_id]["dictamen_riesgo"]
                }
            })

        # Ordenar por puntaje final descendente
        ranking.sort(key=lambda x: x["puntajes"]["final"], reverse=True)
        if ranking:
            ranking[0]["recomendado"] = True

        for r in ranking:
            explicacion = generar_explicacion_resultado(
                proveedor_nombre=r["razon_social"],
                puntajes=r["puntajes"],
                prioridad=prioridad,
                es_recomendado=r["recomendado"],
                costo_total=r["costo_total"],
                tiempo_entrega_dias=r["tiempo_entrega_max_dias"],
                cobertura_pct=r["cobertura_porcentaje"],
                cumplimiento_pct=r["cumplimiento_promedio"]
            )
            r["explicacion"] = explicacion

        ganador = ranking[0] if ranking else None
        
        if ganador:
            conclusion = (
                f"RECOMENDACIÓN FINAL: Se recomienda adjudicar la adquisición a {ganador['razon_social']} "
                f"con un puntaje global de {ganador['puntajes']['final']}/100. "
                f"El proveedor ofrece la mejor combinación evaluada bajo la prioridad '{prioridad}'."
            )
        else:
            conclusion = "No fue posible determinar un proveedor recomendado."

        return {
            "prioridad_aplicada": prioridad,
            "ponderaciones": ponderaciones,
            "conclusion_agente_decisor": conclusion,
            "proveedor_recomendado": ganador,
            "ranking": ranking
        }
