from typing import Dict, Any, Optional
from decimal import Decimal

# Ponderaciones base según la prioridad de la evaluación
PONDERACIONES = {
    "precio": {
        "precio": 0.40,
        "calidad": 0.20,
        "logistica": 0.20,
        "historial": 0.10,
        "riesgo": 0.10
    },
    "calidad": {
        "calidad": 0.40,
        "historial": 0.20,
        "precio": 0.15,
        "logistica": 0.15,
        "riesgo": 0.10
    },
    "logistica": {
        "logistica": 0.40,
        "precio": 0.20,
        "calidad": 0.20,
        "historial": 0.10,
        "riesgo": 0.10
    },
    "balanceado": {
        "precio": 0.25,
        "calidad": 0.25,
        "logistica": 0.20,
        "historial": 0.20,
        "riesgo": 0.10
    }
}

def obtener_ponderaciones(prioridad: Optional[str]) -> Dict[str, float]:
    p = (prioridad or "balanceado").lower().strip()
    return PONDERACIONES.get(p, PONDERACIONES["balanceado"])

def calcular_puntaje_precio(costo_proveedor: float, costo_minimo_todos: float) -> float:
    """
    A menor costo, mayor puntaje. El proveedor con menor costo obtiene 100 puntos.
    """
    if costo_proveedor <= 0 or costo_minimo_todos <= 0:
        return 50.0
    puntaje = (costo_minimo_todos / costo_proveedor) * 100.0
    return min(100.0, max(0.0, round(puntaje, 2)))

def calcular_puntaje_logistica(
    tiempo_proveedor_dias: int,
    tiempo_minimo_todos_dias: int,
    entrega_maxima_dias: Optional[int] = None
) -> float:
    """
    A menor tiempo de entrega, mayor puntaje. Penaliza si excede la entrega máxima solicitada.
    """
    if tiempo_proveedor_dias <= 0 or tiempo_minimo_todos_dias <= 0:
        return 50.0
    
    puntaje = (tiempo_minimo_todos_dias / tiempo_proveedor_dias) * 100.0
    
    # Penalización del 40% si excede el plazo máximo establecido en la evaluación
    if entrega_maxima_dias and entrega_maxima_dias > 0:
        if tiempo_proveedor_dias > entrega_maxima_dias:
            puntaje = puntaje * 0.60
            
    return min(100.0, max(0.0, round(puntaje, 2)))

def calcular_puntaje_calidad(tasa_defectos_promedio: float) -> float:
    """
    Basado en la tasa histórica de defectos. 0% defectos = 100 puntos.
    Cada 1% de defectos resta 15 puntos.
    """
    if tasa_defectos_promedio < 0:
        tasa_defectos_promedio = 0.0
    puntaje = 100.0 - (tasa_defectos_promedio * 15.0)
    return min(100.0, max(0.0, round(puntaje, 2)))

def calcular_puntaje_historial(cumplimiento_promedio: float, total_operaciones: int) -> float:
    """
    Evalúa el cumplimiento de entregas y el volumen de experiencia histórica previa.
    """
    if total_operaciones == 0:
        # Proveedor nuevo sin historial previo parte con puntaje neutro
        return 65.0
    
    # Base de cumplimiento histórico (0-100)
    puntaje_base = cumplimiento_promedio
    
    # Bonificación por consistencia si tiene 2 o más operaciones
    bono_volumen = min(10.0, total_operaciones * 3.0)
    
    puntaje = (puntaje_base * 0.90) + bono_volumen
    return min(100.0, max(0.0, round(puntaje, 2)))

def calcular_puntaje_riesgo(
    cobertura_porcentaje: float,
    cumplimiento_promedio: float,
    total_operaciones: int
) -> float:
    """
    Puntaje de seguridad / bajo riesgo.
    100 = mínimo riesgo (alta cobertura, excelente cumplimiento, historial comprobado).
    """
    # 1. Cobertura de catálogo requerida (50% del peso del riesgo)
    puntaje_cobertura = cobertura_porcentaje
    
    # 2. Historial de cumplimiento (30% del peso del riesgo)
    puntaje_cumplimiento = cumplimiento_promedio if total_operaciones > 0 else 70.0
    
    # 3. Estabilidad y antecedentes (20% del peso del riesgo)
    puntaje_estabilidad = min(100.0, 50.0 + (total_operaciones * 15.0))
    
    riesgo_inverso = (puntaje_cobertura * 0.50) + (puntaje_cumplimiento * 0.30) + (puntaje_estabilidad * 0.20)
    return min(100.0, max(0.0, round(riesgo_inverso, 2)))

def calcular_puntaje_final(puntajes: Dict[str, float], ponderaciones: Dict[str, float]) -> float:
    """
    Calcula la suma ponderada de todas las dimensiones evaluadas.
    """
    score = (
        puntajes.get("precio", 0.0) * ponderaciones.get("precio", 0.25) +
        puntajes.get("calidad", 0.0) * ponderaciones.get("calidad", 0.25) +
        puntajes.get("logistica", 0.0) * ponderaciones.get("logistica", 0.20) +
        puntajes.get("historial", 0.0) * ponderaciones.get("historial", 0.20) +
        puntajes.get("riesgo", 0.0) * ponderaciones.get("riesgo", 0.10)
    )
    return min(100.0, max(0.0, round(score, 2)))

def generar_explicacion_resultado(
    proveedor_nombre: str,
    puntajes: Dict[str, float],
    prioridad: str,
    es_recomendado: bool,
    costo_total: float,
    tiempo_entrega_dias: int,
    cobertura_pct: float,
    cumplimiento_pct: float
) -> str:
    """
    Genera una explicación analítica y transparente de por qué el proveedor obtuvo dicho puntaje y si es recomendado.
    """
    razones = []
    
    if cobertura_pct == 100.0:
        razones.append("ofrece el 100% de los productos solicitados")
    else:
        razones.append(f"cubre el {cobertura_pct}% de los productos")

    razones.append(f"costo total de S/ {costo_total:,.2f}")
    razones.append(f"plazo logístico de {tiempo_entrega_dias} días")
    
    if cumplimiento_pct > 0:
        razones.append(f"desempeño histórico con {cumplimiento_pct:.1f}% de cumplimiento")
    else:
        razones.append("sin operaciones históricas registradas")

    resumen = (
        f"Puntaje Final: {puntajes['final']} / 100 (Precio: {puntajes['precio']}, "
        f"Calidad: {puntajes['calidad']}, Logística: {puntajes['logistica']}, "
        f"Historial: {puntajes['historial']}, Riesgo: {puntajes['riesgo']}). "
        f"Evaluado bajo criterio de prioridad '{prioridad}'. "
    )

    if es_recomendado:
        justificacion = f"PROVEEDOR RECOMENDADO: {proveedor_nombre} destaca por ser la opción óptima integral: {', '.join(razones)}. {resumen}"
    else:
        justificacion = f"Opción alterna: {proveedor_nombre}. {resumen} Detalles: {', '.join(razones)}."

    return justificacion
