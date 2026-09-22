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

El sistema deja preparada, pero **desactivada por defecto**, la arquitectura
para integrar Claude (Anthropic) como componente complementario:

- `app/ai/llm_client.py`: interfaz (`LLMClient`) y contratos (`LLMRequest`,
  `LLMResponse`) para una futura comunicación con la API de Anthropic. No
  realiza ninguna llamada de red; `generate()` valida disponibilidad y
  delega en `_llamar_anthropic()`, que lanza `NotImplementedError` porque su
  implementación real corresponde a la **Fase 12**.
- `app/ai/parser_solicitud.py`: transforma una solicitud en lenguaje natural
  en una estructura (`SolicitudInterpretada`) utilizable por el sistema de
  evaluación. Mientras Claude no esté activo, usa una extracción heurística
  determinística (expresiones regulares) como piso funcional.
- `app/ai/prompts/*.txt`: plantillas preparatorias con el rol, la
  información disponible y las restricciones de cada agente
  (financiero, calidad, logístico, riesgo, decisor), listas para que la
  Fase 12 las use al invocar Claude.

### Variables de entorno relevantes

```text
LLM_ENABLED=false       # false = modo determinístico puro (por defecto)
ANTHROPIC_API_KEY=      # se deja vacía; nunca se sube al repositorio
CLAUDE_MODEL=claude-sonnet-5
CLAUDE_MAX_TOKENS=1024
CLAUDE_TEMPERATURE=0.2
```

Con `LLM_ENABLED=false` (o sin `ANTHROPIC_API_KEY`), el backend inicia y
funciona con normalidad: el motor determinístico (F7) y los agentes
especializados (F8) siguen siendo la única fuente de puntajes y
recomendaciones. **Claude todavía no está integrado**; esa integración real
(llamadas efectivas a la API de Anthropic) corresponde a la Fase 12.
