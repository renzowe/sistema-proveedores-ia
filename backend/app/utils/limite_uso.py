"""
Límite de uso en memoria para endpoints públicos que consumen presupuesto
(p. ej. el asistente conversacional con la API de Anthropic).

Aplica dos topes:
- Por cliente (IP): como máximo `limite_por_cliente` peticiones en una
  ventana deslizante de `ventana_segundos`.
- Global diario: como máximo `limite_diario` peticiones por día (UTC), sumando
  todos los clientes. Es el tope que protege el presupuesto aunque alguien
  cambie de IP.

El estado vive en memoria del proceso: se reinicia al reiniciar el backend y
no se comparte entre varias instancias. Es suficiente para una sola instancia
(Render plan gratuito / un contenedor).
"""

import math
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Deque, Dict

from fastapi import HTTPException, Request, status


class LimitadorUso:
    def __init__(
        self,
        limite_por_cliente: Callable[[], int],
        ventana_segundos: Callable[[], int],
        limite_diario: Callable[[], int],
        aviso_por_cliente: str = "Has enviado demasiados mensajes seguidos. Espera {espera} antes de volver a escribir.",
    ) -> None:
        # Los límites se leen en cada llamada (no se copian al construir) para
        # que la configuración pueda cambiarse en pruebas sin recrear el objeto.
        self._limite_por_cliente = limite_por_cliente
        self._ventana_segundos = ventana_segundos
        self._limite_diario = limite_diario
        self._aviso_por_cliente = aviso_por_cliente
        self._lock = threading.Lock()
        self._por_cliente: Dict[str, Deque[float]] = {}
        self._dia_actual = ""
        self._contador_diario = 0

    def registrar(self, cliente: str) -> None:
        """Registra una petición del cliente o lanza HTTP 429 si supera algún límite."""
        self._procesar(cliente, anotar=True)

    def comprobar(self, cliente: str) -> None:
        """Lanza HTTP 429 si el cliente ya alcanzó algún límite, sin contar esta petición."""
        self._procesar(cliente, anotar=False)

    def _procesar(self, cliente: str, anotar: bool) -> None:
        ahora = time.monotonic()
        hoy = datetime.now(timezone.utc).date().isoformat()
        ventana = self._ventana_segundos()

        with self._lock:
            if hoy != self._dia_actual:
                self._dia_actual = hoy
                self._contador_diario = 0

            if self._contador_diario >= self._limite_diario():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="El asistente alcanzó su límite de uso diario. Vuelve a intentarlo mañana; el formulario sigue disponible.",
                )

            marcas = self._por_cliente.setdefault(cliente, deque())
            while marcas and ahora - marcas[0] >= ventana:
                marcas.popleft()

            if len(marcas) >= self._limite_por_cliente():
                espera = int(ventana - (ahora - marcas[0])) + 1
                minutos = math.ceil(espera / 60)
                texto_espera = f"{espera} segundos" if espera < 60 else f"{minutos} minuto{'s' if minutos > 1 else ''}"
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._aviso_por_cliente.format(espera=texto_espera),
                    headers={"Retry-After": str(espera)},
                )

            if not anotar:
                return

            marcas.append(ahora)
            self._contador_diario += 1

            # Evita que el diccionario crezca sin fin con clientes inactivos.
            if len(self._por_cliente) > 10_000:
                self._por_cliente = {
                    c: m for c, m in self._por_cliente.items() if m and ahora - m[-1] < ventana
                }

    def reiniciar(self) -> None:
        with self._lock:
            self._por_cliente.clear()
            self._dia_actual = ""
            self._contador_diario = 0


def obtener_ip_cliente(request: Request) -> str:
    # Detrás del proxy de Render, request.client es el proxy: la IP real del
    # cliente es la última entrada de X-Forwarded-For (la que agrega el proxy;
    # las anteriores las puede falsificar el propio cliente).
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[-1].strip()
    return request.client.host if request.client else "desconocido"
