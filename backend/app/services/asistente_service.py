"""
Servicio del asistente conversacional (Claude, vía API de Anthropic) para la
pestaña Evaluaciones.

Este servicio NO crea ni procesa evaluaciones, y NO calcula puntajes ni
recomendaciones: solo (a) ayuda a armar, turno a turno, el borrador de una
evaluación nueva a partir de una conversación en lenguaje natural, y (b)
explica resultados YA calculados y persistidos por el motor determinístico.
La creación/ejecución real de la evaluación sigue pasando siempre por
`EvaluacionService.crear()` + `EvaluacionService.ejecutar_evaluacion()`.

Mientras no haya una `ANTHROPIC_API_KEY` real configurada (o si la llamada al
LLM falla), cada turno cae a un "modo demostración" determinístico (sin
llamadas externas): reutiliza el parser heurístico ya existente
(`app.ai.parser_solicitud.interpretar_solicitud`) para el borrador, y una
plantilla de texto basada únicamente en datos reales para la explicación.
Esto permite probar todo el flujo de sincronización chat/formulario sin
credenciales, y las pruebas automatizadas nunca dependen de una llamada real.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient, LLMRequest, LLMUnavailableError
from app.ai.parser_solicitud import interpretar_solicitud
from app.models.producto import Producto
from app.schemas.asistente import (
    MAX_CARACTERES_DESCRIPCION,
    MAX_CARACTERES_ESPECIFICACIONES,
    MAX_CARACTERES_NOMBRE_PRODUCTO,
    MAX_CARACTERES_TITULO,
    MAX_PRODUCTOS_BORRADOR,
    AsistenteMensajeIn,
    AsistenteMensajeOut,
    BorradorEvaluacion,
    MensajeChatIn,
    ProductoBorrador,
)
from app.services.evaluacion_service import (
    EvaluacionService,
    _buscar_producto_similar,
    _datos_reales_para_explicacion,
)

_PROMPT_ASISTENTE_PATH = Path(__file__).resolve().parent.parent / "ai" / "prompts" / "asistente.txt"
_PROMPT_DECISOR_PATH = Path(__file__).resolve().parent.parent / "ai" / "prompts" / "decisor.txt"
_MAPA_ROLES_ANTHROPIC = {"usuario": "user", "asistente": "assistant"}
_NOMBRES_CRITERIOS = {
    "precio": "precio",
    "calidad": "calidad",
    "logistica": "logística",
    "historial": "historial",
    "riesgo": "riesgo",
}


def _extraer_json(texto_respuesta: str) -> dict:
    """Limpia envoltorios comunes (fences de markdown) antes de parsear JSON."""
    limpio = texto_respuesta.strip()
    if limpio.startswith("```"):
        limpio = re.sub(r"^```(?:json)?", "", limpio).rstrip("`").strip()
    return json.loads(limpio)


def _texto_recortado(valor: Any, maximo: int) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto[:maximo] or None


def _entero_o_none(valor: Any) -> Optional[int]:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


class AsistenteService:
    @staticmethod
    def estado(
        permitir_llm: bool = True,
        requiere_codigo: bool = False,
        codigo_valido: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        `permitir_llm` es False cuando hace falta un código de acceso y la
        petición no trae uno válido: entonces el chat funciona en modo
        demostración aunque haya una API Key configurada.
        """
        llm_client = LLMClient()
        llm_configurado = llm_client.esta_disponible()
        disponible = llm_configurado and permitir_llm
        return {
            "modo": "real" if disponible else "demostracion",
            "proveedor": "anthropic",
            "modelo": llm_client.model if disponible else None,
            "requiere_codigo": requiere_codigo and llm_configurado,
            "codigo_valido": codigo_valido,
        }

    @staticmethod
    def procesar_mensaje(db: Session, payload: AsistenteMensajeIn, permitir_llm: bool = True) -> AsistenteMensajeOut:
        if not payload.mensajes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La conversación debe incluir al menos un mensaje."
            )

        if payload.mensajes[-1].rol != "usuario":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El último mensaje de la conversación debe ser del usuario."
            )

        ultimo_mensaje = payload.mensajes[-1].contenido.strip()
        if not ultimo_mensaje:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El mensaje no puede estar vacío."
            )

        if payload.evaluacion_id is not None:
            return AsistenteService._modo_explicacion(db, payload, permitir_llm)
        return AsistenteService._modo_borrador(db, payload, permitir_llm)

    # --- Modo "explicar resultados" (contexto = evaluación ya existente) ---

    @staticmethod
    def _modo_explicacion(db: Session, payload: AsistenteMensajeIn, permitir_llm: bool) -> AsistenteMensajeOut:
        evaluacion = EvaluacionService.obtener_por_id(db, payload.evaluacion_id)
        resultados = EvaluacionService.obtener_resultados(db, payload.evaluacion_id)

        if not resultados.get("ranking"):
            respuesta = (
                f'La evaluación "{evaluacion.titulo}" todavía no ha sido procesada, así que '
                "no tengo resultados reales que explicar. Procésala con el botón "
                '"Procesar" y vuelve a preguntarme.'
            )
            return AsistenteMensajeOut(
                respuesta=respuesta,
                borrador=payload.borrador,
                campos_actualizados=[],
                listo_para_confirmar=False,
                modo="demostracion",
                contexto_evaluacion_id=payload.evaluacion_id,
            )

        compatibles = EvaluacionService.buscar_proveedores_compatibles(db, payload.evaluacion_id)
        cobertura = {
            p["proveedor_id"]: {
                "cobertura_porcentaje": p["cobertura_porcentaje"],
                "productos_faltantes": [f["nombre_producto"] for f in p["productos_faltantes"]],
            }
            for p in compatibles["proveedores_compatibles"]
        }
        datos_reales = _datos_reales_para_explicacion(resultados, cobertura)
        llm_client = LLMClient()

        if permitir_llm and llm_client.esta_disponible():
            respuesta_real = AsistenteService._explicacion_real(llm_client, payload, datos_reales)
            if respuesta_real is not None:
                return AsistenteMensajeOut(
                    respuesta=respuesta_real,
                    borrador=payload.borrador,
                    campos_actualizados=[],
                    listo_para_confirmar=False,
                    modo="real",
                    contexto_evaluacion_id=payload.evaluacion_id,
                )

        respuesta_demo = AsistenteService._explicacion_demostracion(datos_reales)
        return AsistenteMensajeOut(
            respuesta=respuesta_demo,
            borrador=payload.borrador,
            campos_actualizados=[],
            listo_para_confirmar=False,
            modo="demostracion",
            contexto_evaluacion_id=payload.evaluacion_id,
        )

    @staticmethod
    def _explicacion_real(
        llm_client: LLMClient,
        payload: AsistenteMensajeIn,
        datos_reales: Dict[str, Any],
    ) -> Optional[str]:
        prompt_base = _PROMPT_DECISOR_PATH.read_text(encoding="utf-8")
        prompt_sistema = (
            f"{prompt_base}\n\n"
            "Además de explicar la conclusión, aquí estás respondiendo dentro de una "
            "conversación: el usuario puede hacer preguntas de seguimiento sobre este "
            "mismo resultado. Responde solo con texto en español (no JSON), en texto "
            "plano: el chat no interpreta Markdown, así que no uses asteriscos, "
            "almohadillas ni listas con guiones.\n\n"
            "DATOS REALES DE ESTA EVALUACIÓN (única fuente permitida; no uses ningún "
            "dato fuera de este bloque):\n"
            f"{json.dumps(datos_reales, ensure_ascii=False, indent=2)}"
        )
        historial, mensaje_actual = AsistenteService._preparar_turno(payload.mensajes)
        try:
            respuesta = llm_client.generate(LLMRequest(
                prompt=mensaje_actual,
                system=prompt_sistema,
                historial=historial,
                contexto=datos_reales,
                agente="decisor",
            ))
        except LLMUnavailableError:
            return None
        return respuesta.contenido

    @staticmethod
    def _explicacion_demostracion(datos_reales: Dict[str, Any]) -> str:
        ranking = datos_reales.get("ranking") or []
        if not ranking:
            return "[Modo demostración] No hay proveedores en el ranking de esta evaluación."

        ganador = next((r for r in ranking if r["recomendado"]), ranking[0])
        puntajes = ganador["puntajes"]
        partes = [
            f'[Modo demostración — sin IA real] Para "{datos_reales["titulo"]}" '
            f'(prioridad: {datos_reales["prioridad_aplicada"]}), el proveedor recomendado es '
            f'{ganador["proveedor"]}, con un puntaje final de {puntajes["final"]:.1f}/100.'
        ]

        top_criterios = sorted(
            ((k, v) for k, v in puntajes.items() if k != "final"),
            key=lambda kv: kv[1],
            reverse=True,
        )[:2]
        if top_criterios:
            detalle = " y ".join(f"{_NOMBRES_CRITERIOS.get(k, k)} ({v:.1f})" for k, v in top_criterios)
            partes.append(f"Los criterios que más influyeron fueron {detalle}.")

        for r in ranking:
            if r["puntajes"]["final"] > puntajes["final"] and r.get("cobertura_porcentaje", 100) < 100:
                faltantes = ", ".join(r.get("productos_faltantes") or [])
                partes.append(
                    f'{r["proveedor"]} obtuvo más puntaje ({r["puntajes"]["final"]:.1f}), pero no puede '
                    f"recomendarse porque no ofrece todos los productos solicitados (le falta: {faltantes})."
                )

        if len(ranking) > 1:
            partes.append(f"Se compararon {len(ranking)} proveedores en total.")

        return " ".join(partes)

    # --- Modo "armar borrador" (sin evaluación de contexto) -----------------

    @staticmethod
    def _modo_borrador(db: Session, payload: AsistenteMensajeIn, permitir_llm: bool) -> AsistenteMensajeOut:
        llm_client = LLMClient()
        modo = "demostracion"
        resultado = None

        if permitir_llm and llm_client.esta_disponible():
            resultado = AsistenteService._turno_real(llm_client, payload)
            if resultado is not None:
                modo = "real"

        if resultado is None:
            resultado = AsistenteService._turno_demostracion(payload.borrador, payload.mensajes[-1].contenido.strip())

        respuesta_texto, borrador_bruto, campos_actualizados = resultado

        # El borrador puede venir del LLM: se valida y recorta campo a campo
        # para que una respuesta mal formada nunca produzca un error 500.
        productos_brutos = borrador_bruto.get("productos")
        if not isinstance(productos_brutos, list):
            productos_brutos = []

        catalogo = db.query(Producto).filter(Producto.estado == "Activo").all()
        productos_resueltos: List[ProductoBorrador] = []
        for p in productos_brutos[:MAX_PRODUCTOS_BORRADOR]:
            if not isinstance(p, dict):
                continue
            nombre = _texto_recortado(p.get("nombre_detectado"), MAX_CARACTERES_NOMBRE_PRODUCTO)
            if not nombre:
                continue
            coincidencia = _buscar_producto_similar(nombre, catalogo)
            productos_resueltos.append(ProductoBorrador(
                nombre_detectado=nombre,
                cantidad=max(_entero_o_none(p.get("cantidad")) or 1, 1),
                especificaciones=_texto_recortado(p.get("especificaciones"), MAX_CARACTERES_ESPECIFICACIONES),
                producto_id=coincidencia.id if coincidencia else None,
                producto_nombre_catalogo=coincidencia.nombre if coincidencia else None,
                sin_coincidencia=coincidencia is None,
            ))

        prioridad = borrador_bruto.get("prioridad") or "balanceado"
        if prioridad not in {"precio", "calidad", "logistica", "balanceado"}:
            prioridad = "balanceado"

        plazo = _entero_o_none(borrador_bruto.get("entrega_maxima_dias"))
        borrador_final = BorradorEvaluacion(
            titulo=_texto_recortado(borrador_bruto.get("titulo"), MAX_CARACTERES_TITULO),
            descripcion_necesidad=_texto_recortado(borrador_bruto.get("descripcion_necesidad"), MAX_CARACTERES_DESCRIPCION),
            entrega_maxima_dias=plazo if plazo and plazo > 0 else None,
            prioridad=prioridad,
            productos=productos_resueltos,
        )

        listo_para_confirmar = bool(
            borrador_final.titulo
            and borrador_final.productos
            and all(p.producto_id is not None for p in borrador_final.productos)
        )

        return AsistenteMensajeOut(
            respuesta=respuesta_texto,
            borrador=borrador_final,
            campos_actualizados=campos_actualizados,
            listo_para_confirmar=listo_para_confirmar,
            modo=modo,
            contexto_evaluacion_id=None,
        )

    @staticmethod
    def _preparar_turno(mensajes: List[MensajeChatIn]) -> Tuple[List[Dict[str, str]], str]:
        """
        Devuelve (historial, mensaje_actual) en el formato de la API de Anthropic.

        La API exige que la conversación empiece con un mensaje del usuario y
        que los roles se alternen. El frontend solo reenvía los últimos
        mensajes (el recorte puede empezar por una respuesta del asistente) y
        un turno fallido deja dos mensajes de usuario seguidos, así que se
        descartan las respuestas iniciales y se unen los mensajes consecutivos
        del mismo rol. `procesar_mensaje` ya garantiza que el último es del usuario.
        """
        turnos: List[Dict[str, str]] = []
        for m in mensajes:
            rol = _MAPA_ROLES_ANTHROPIC[m.rol]
            if not turnos and rol == "assistant":
                continue
            if turnos and turnos[-1]["role"] == rol:
                turnos[-1]["content"] += f"\n\n{m.contenido}"
            else:
                turnos.append({"role": rol, "content": m.contenido})
        actual = turnos.pop()
        return turnos, actual["content"]

    @staticmethod
    def _turno_real(llm_client: LLMClient, payload: AsistenteMensajeIn) -> Optional[Tuple[str, Dict[str, Any], List[str]]]:
        prompt_sistema = _PROMPT_ASISTENTE_PATH.read_text(encoding="utf-8")
        historial, mensaje_actual = AsistenteService._preparar_turno(payload.mensajes)
        borrador_actual_json = json.dumps(payload.borrador.model_dump(), ensure_ascii=False)
        prompt_usuario = (
            f"Borrador actual antes de este turno:\n{borrador_actual_json}\n\n"
            f"Mensaje del usuario:\n{mensaje_actual}"
        )

        try:
            respuesta = llm_client.generate(LLMRequest(
                prompt=prompt_usuario,
                system=prompt_sistema,
                historial=historial,
                agente="interprete",
            ))
        except LLMUnavailableError:
            return None

        try:
            datos = _extraer_json(respuesta.contenido)
            borrador_llm = datos.get("borrador") or {}
            if not isinstance(borrador_llm, dict):
                return None
            respuesta_texto = str(datos.get("respuesta_usuario", "")).strip()
            if not respuesta_texto:
                return None
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None

        campos_actualizados = AsistenteService._diferencias(payload.borrador, borrador_llm)
        return respuesta_texto, borrador_llm, campos_actualizados

    @staticmethod
    def _diferencias(previo: BorradorEvaluacion, nuevo: Dict[str, Any]) -> List[str]:
        campos = []
        for campo in ("titulo", "descripcion_necesidad", "entrega_maxima_dias", "prioridad"):
            if nuevo.get(campo) != getattr(previo, campo):
                campos.append(campo)

        productos_previos = [
            {"nombre_detectado": p.nombre_detectado, "cantidad": p.cantidad, "especificaciones": p.especificaciones}
            for p in previo.productos
        ]
        if (nuevo.get("productos") or []) != productos_previos:
            campos.append("productos")
        return campos

    @staticmethod
    def _turno_demostracion(borrador_previo: BorradorEvaluacion, ultimo_mensaje: str) -> Tuple[str, Dict[str, Any], List[str]]:
        interpretado = interpretar_solicitud(ultimo_mensaje)
        campos_actualizados: List[str] = []

        descripcion = borrador_previo.descripcion_necesidad
        if descripcion is None:
            descripcion = ultimo_mensaje
            campos_actualizados.append("descripcion_necesidad")

        entrega_maxima_dias = borrador_previo.entrega_maxima_dias
        if entrega_maxima_dias is None and interpretado.entrega_maxima_dias is not None:
            entrega_maxima_dias = interpretado.entrega_maxima_dias
            campos_actualizados.append("entrega_maxima_dias")

        prioridad = borrador_previo.prioridad
        if prioridad == "balanceado" and interpretado.prioridad_sugerida != "balanceado":
            prioridad = interpretado.prioridad_sugerida
            campos_actualizados.append("prioridad")

        productos_nuevos = [
            {"nombre_detectado": p.nombre_detectado, "cantidad": p.cantidad, "especificaciones": p.especificaciones}
            for p in borrador_previo.productos
        ]
        if interpretado.productos:
            productos_nuevos.extend({
                "nombre_detectado": p.nombre_detectado,
                "cantidad": p.cantidad,
                "especificaciones": p.especificaciones,
            } for p in interpretado.productos)
            campos_actualizados.append("productos")

        faltantes = []
        if not borrador_previo.titulo:
            faltantes.append("un título breve para la solicitud")
        if not productos_nuevos:
            faltantes.append("al menos un producto con cantidad")

        if faltantes:
            respuesta = (
                "[Modo demostración — sin IA real] Entendí lo que pude con reglas simples. "
                f"Todavía falta: {', '.join(faltantes)}."
            )
        else:
            respuesta = (
                "[Modo demostración — sin IA real] Con esto el borrador ya tiene título y al "
                "menos un producto. Revisa el panel y confirma cuando quieras evaluar."
            )

        borrador_dict = {
            "titulo": borrador_previo.titulo,
            "descripcion_necesidad": descripcion,
            "entrega_maxima_dias": entrega_maxima_dias,
            "prioridad": prioridad,
            "productos": productos_nuevos,
        }
        return respuesta, borrador_dict, campos_actualizados
