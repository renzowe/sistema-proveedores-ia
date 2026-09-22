# Sistema Inteligente Agéntico para la Evaluación y Selección de Proveedores mediante IA

Sistema web de apoyo a la decisión para evaluar proveedores y obtener recomendaciones basadas en múltiples criterios determinísticos y asistencia mediante IA.

## Requisitos Previos

- Python 3.10+
- PostgreSQL (Base de datos creada: `sistema-proveedores-ia`)

## Configuración e Instalación Local

1. Configurar la base de datos PostgreSQL local.
2. Navegar a la carpeta `backend` e instalar dependencias:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. Configurar las variables de entorno en `backend/.env`.
4. Ejecutar el servidor FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Abrir la interfaz frontend abriendo `frontend/index.html` en un navegador web o sirviéndola localmente.

## Estructura del Proyecto

- `backend/`: API REST construida con FastAPI, SQLAlchemy y arquitectura de agentes.
- `frontend/`: Interfaz de usuario construida con HTML, CSS y JavaScript nativo.

## Inteligencia Artificial (Claude)

El proyecto deja preparada la arquitectura para integrar Claude mediante la
API de Anthropic (`backend/app/ai/`), pero **esa integración real todavía no
está activa**. Por defecto (`LLM_ENABLED=false`), el sistema funciona de
forma completa con el motor determinístico y los agentes especializados, sin
depender de ninguna API externa ni credencial. Ver `backend/README.md` para
el detalle de esta capa y las variables de entorno asociadas.
