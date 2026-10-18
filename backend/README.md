# Backend - Sistema Inteligente Agéntico para Evaluación de Proveedores

Backend desarrollado con **Python + FastAPI + SQLAlchemy + PostgreSQL**.

## Estructura

```text
backend/app/
├── main.py              # Punto de entrada de FastAPI
├── config.py            # Variables de entorno y configuración
├── database.py          # Conexión a PostgreSQL con SQLAlchemy
├── models/              # Modelos ORM SQLAlchemy
├── schemas/             # Schemas Pydantic para validación y DTOs
├── routers/             # Endpoints HTTP REST
├── services/            # Lógica de negocio
├── agents/              # Agentes inteligentes (orquestador, financiero, etc.)
├── ai/                  # Integración con LLM y parser de lenguaje natural
└── utils/               # Funciones de cálculo y validaciones
```

## Ejecución Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Capa de IA (`app/ai/`) — estado actual

El sistema está preparado para integrar **Claude** (API de Anthropic) como
componente complementario del motor determinístico. La implementación es
real (no un stub): lo único que falta para activarla es una
`ANTHROPIC_API_KEY` válida. Puede **desactivarse por completo** mediante
`LLM_ENABLED=false` sin afectar el resto del sistema:

- `app/ai/llm_client.py`: interfaz (`LLMClient`) y contratos (`LLMRequest`,
  `LLMResponse`) para la comunicación real con Claude vía el SDK
  `anthropic`. `generate()` valida disponibilidad y delega en
  `_llamar_claude()`. Cualquier error (red, cuota, autenticación) se
  traduce a `LLMUnavailableError` para que el llamador caiga al modo
  determinístico sin interrumpir el flujo principal.
- `app/ai/parser_solicitud.py`: transforma una solicitud en lenguaje natural
  en una estructura (`SolicitudInterpretada`) utilizable por el sistema de
  evaluación. Si el LLM está disponible, le pide un JSON estructurado; si no
  responde, falla, o está desactivado, usa una extracción heurística
  determinística (expresiones regulares) como piso funcional que nunca
  depende de un servicio externo.
- `app/ai/prompts/*.txt`: plantillas con el rol, la información disponible
  y las restricciones de cada agente (financiero, calidad, logístico,
  riesgo, decisor, asistente). `AsistenteService` usa `asistente.txt` (armar
  borrador) y `decisor.txt` (explicar resultados); el resto documenta el rol
  de cada agente del motor determinístico.

Estas dos capacidades (interpretar solicitudes y explicar resultados) viven
dentro del **asistente conversacional** de la pestaña Evaluaciones — no
están expuestas como campos sueltos en los formularios del frontend.

### Asistente conversacional (`POST /evaluaciones/asistente/mensaje`, `GET /evaluaciones/asistente/estado`)

`GET /evaluaciones/asistente/estado` devuelve `{"modo": "real" | "demostracion", ...}`
según haya o no un LLM disponible; el chat lo usa para mostrar desde el
inicio el distintivo "Modo demostración" o un aviso si no hay conexión.

`app/services/asistente_service.py` (`AsistenteService.procesar_mensaje`) es
el servicio detrás del chat de la pestaña Evaluaciones. Un solo endpoint
cubre dos modos, distinguidos por si el payload trae `evaluacion_id`:

- **Sin `evaluacion_id`** ("armar borrador"): el chat ayuda, turno a turno, a
  completar un borrador de evaluación nueva (título, descripción, plazo,
  prioridad, productos). El backend resuelve cada producto detectado contra
  el catálogo real (reutiliza `_buscar_producto_similar`) — el LLM nunca
  decide `producto_id`. La creación/ejecución real de la evaluación sigue
  pasando siempre por `EvaluacionService.crear()` + `ejecutar_evaluacion()`
  cuando el usuario confirma desde el formulario.
- **Con `evaluacion_id`**: el chat explica los resultados YA calculados y
  persistidos de esa evaluación (reutiliza `EvaluacionService.obtener_resultados()`,
  recortado por `_datos_reales_para_explicacion()` a solo ranking y puntajes).
  Si la evaluación no fue procesada, responde pidiendo procesarla — nunca
  inventa un resultado.

**Modo demostración**: mientras `LLM_ENABLED=false` o no haya
`ANTHROPIC_API_KEY` (o si la llamada real a Claude falla), cada turno cae a
una respuesta determinística sin llamadas externas: el parser heurístico ya
existente (`app.ai.parser_solicitud.interpretar_solicitud`) para el modo
borrador, y una plantilla basada únicamente en datos reales para el modo
explicación. La respuesta siempre llega marcada con `"modo": "demostracion"`
y el texto incluye el prefijo `[Modo demostración — sin IA real]` — nunca se
presenta como si fuera una respuesta real de Claude. Las pruebas
automatizadas (`backend/tests/test_asistente.py`) corren siempre en este
modo, sin credenciales ni llamadas externas.

**Para activar el modo real**, sin tocar ningún archivo de código: configura
`ANTHROPIC_API_KEY` y `LLM_ENABLED=true` en `backend/.env` (o en las
variables de entorno de Render) y reinicia el backend. Cada turno intentará
primero una llamada real a Claude (multi-turno, vía `LLMRequest.historial`/
`system` en `app/ai/llm_client.py`) y solo cae al modo demostración si esa
llamada falla o no está disponible.

**Protección del endpoint** (es público y, con API Key, cada mensaje cuesta):
- Código de acceso (`ASISTENTE_CODIGO_ACCESO`): si está definido, solo las
  peticiones con la cabecera `X-Codigo-Asistente` correcta usan Claude; el
  resto responde en modo demostración, sin consumir la API Key. El chat lo
  pide con el botón "Usar Claude" y lo recuerda mientras la pestaña esté
  abierta (`sessionStorage`). Se compara en tiempo constante y se permiten
  `ASISTENTE_INTENTOS_CODIGO` intentos fallidos por IP en la ventana del
  limitador (después, HTTP 429). Vacío = no se pide código; si además Claude
  está activo, el backend lo advierte en los registros al arrancar.
- Límite de uso en memoria (`app/utils/limite_uso.py`): como máximo
  `ASISTENTE_LIMITE_POR_IP` mensajes por IP cada `ASISTENTE_VENTANA_SEGUNDOS`,
  y `ASISTENTE_LIMITE_DIARIO` mensajes por día sumando todos los clientes.
  Al superarlo responde `429`. El contador se reinicia al reiniciar el backend
  y no se comparte entre instancias (suficiente para una sola instancia).
- Tamaño acotado (`app/schemas/asistente.py`): mensajes de hasta 2000
  caracteres y como máximo 30 mensajes por petición (`422` si se supera). El
  chat solo reenvía los últimos 20.

### Variables de entorno relevantes

```text
LLM_ENABLED=false       # false = modo determinístico puro (por defecto)
ANTHROPIC_API_KEY=      # se deja vacía; nunca se sube al repositorio
CLAUDE_MODEL=claude-haiku-4-5-20251001
CLAUDE_MAX_TOKENS=1024

CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500   # en producción: URL pública del frontend
ASISTENTE_LIMITE_POR_IP=20
ASISTENTE_VENTANA_SEGUNDOS=600
ASISTENTE_LIMITE_DIARIO=200
ASISTENTE_CODIGO_ACCESO=   # en producción: obligatorio antes de LLM_ENABLED=true
ASISTENTE_INTENTOS_CODIGO=5
```

`CORS_ORIGINS` define qué dominios pueden llamar a la API desde el navegador.
Si en producción no incluye la URL del frontend, el navegador bloqueará las
peticiones y la interfaz mostrará "Backend no disponible".

Con `LLM_ENABLED=false` (o sin `ANTHROPIC_API_KEY`), el backend inicia y
funciona con normalidad: el motor determinístico (F7) y los agentes
especializados (F8) siguen siendo la única fuente de puntajes y
recomendaciones. Claude solo produce texto complementario (interpretación de
solicitudes y explicaciones) a partir de datos ya calculados — nunca decide
puntajes ni recomendaciones.
