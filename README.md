# Sistema Inteligente Agéntico para la Evaluación y Selección de Proveedores mediante IA

Sistema web de apoyo a la decisión para evaluar proveedores y obtener recomendaciones basadas en múltiples criterios determinísticos y asistencia mediante IA.

## Ejecución con Docker (recomendada)

Levanta el sistema completo (base de datos PostgreSQL, backend y frontend) con
los datos de ejemplo ya cargados. No requiere instalar Python ni PostgreSQL,
ni ninguna cuenta o credencial.

**Requisito:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
instalado y abierto.

1. Clonar el repositorio y entrar en la carpeta:
   ```bash
   git clone <url-del-repositorio>
   cd sistema-proveedores-ia
   ```
2. Crear el archivo de configuración `.env` a partir del ejemplo:
   ```bash
   cp .env.example .env        # Windows (cmd): copy .env.example .env
   ```
   y en `.env` escribir una contraseña inventada (sin espacios) en
   `POSTGRES_DOCKER_PASSWORD=`. Es la contraseña de la base de datos que Docker
   crea en esa computadora; `.env` no se sube al repositorio.
3. Construir y arrancar (la primera vez tarda unos minutos):
   ```bash
   docker compose up -d --build
   ```
   Las siguientes veces basta con `docker compose up -d`.
4. Abrir **http://localhost:8080** en el navegador.
   - Documentación interactiva de la API: http://localhost:8080/docs

Comandos útiles:

| Acción | Comando |
|---|---|
| Arrancar en segundo plano | `docker compose up -d --build` |
| Detener | `docker compose down` |
| Detener y **borrar los datos** (vuelve a los datos de ejemplo) | `docker compose down -v` |
| Ver los registros del backend | `docker compose logs -f backend` |
| Ejecutar las pruebas automatizadas | `docker compose run --rm backend python -m pytest -q` |

Las pruebas se ejecutan contra la base de datos del contenedor, nunca contra
una base de producción.

**Configuración opcional** (en el mismo `.env`): cambiar el puerto
(`FRONTEND_PORT`, si el 8080 está ocupado) o activar el asistente con Claude
real (`LLM_ENABLED=true` y `ANTHROPIC_API_KEY`). Sin API Key, el asistente
funciona en modo demostración. Tras cambiar `.env`, aplicar con
`docker compose up -d`.

**Arquitectura de los contenedores:**

```
navegador ──► frontend (nginx, puerto 8080) ──/api──► backend (FastAPI) ──► db (PostgreSQL)
```

El navegador solo se comunica con nginx, que sirve la interfaz y reenvía las
llamadas `/api` al backend. La base de datos guarda sus datos en un volumen de
Docker, así que se conservan al detener y volver a arrancar. En producción, la
misma imagen del backend puede conectarse a una base gestionada (p. ej. Neon)
cambiando solo `DATABASE_URL`, sin `SEED_DATA`.

## Ejecución sin Docker (desarrollo)

Requisitos: Python (probado con 3.14, la misma versión de la imagen Docker) y
una base PostgreSQL.

1. Instalar dependencias del backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Copiar `backend/.env.example` a `backend/.env` y configurar `DATABASE_URL`
   (obligatoria: sin ella el backend no arranca).
3. (Opcional) cargar datos de ejemplo:
   ```bash
   python -m app.utils.seed_data
   python -m app.utils.seed_historial
   ```
4. Ejecutar el backend:
   ```bash
   uvicorn app.main:app --reload
   ```
5. En otra terminal, servir el frontend y abrir http://localhost:5500:
   ```bash
   cd frontend
   python -m http.server 5500
   ```
   (Abrir `index.html` directamente como archivo no funciona: el backend solo
   acepta peticiones de los orígenes configurados en `CORS_ORIGINS`.)

> Nota: `pytest` sin Docker usa la base de datos de `backend/.env`. Las pruebas
> crean y borran datos, así que no deben apuntar a una base de producción.

## Estructura del Proyecto

- `backend/`: API REST construida con FastAPI, SQLAlchemy y arquitectura de agentes (con su `Dockerfile`).
- `frontend/`: Interfaz de usuario construida con HTML, CSS y JavaScript nativo (con su `Dockerfile` y `nginx.conf`).
- `docker-compose.yml`: orquesta base de datos, backend y frontend para la ejecución local.

## Inteligencia Artificial (Claude)

El proyecto integra un **asistente conversacional** (Claude, vía API de
Anthropic) en la pestaña Evaluaciones (`backend/app/ai/` +
`AsistenteService`): ayuda a armar el borrador de una evaluación en
lenguaje natural y a explicar resultados ya calculados, sin participar en
el cálculo de puntajes ni en la recomendación — eso siempre lo decide el
motor determinístico. Mientras no haya una `ANTHROPIC_API_KEY` real
configurada, el asistente funciona igual en un **modo demostración**
determinístico (sin llamadas externas), claramente marcado en cada
respuesta. Puede desactivarse por completo con `LLM_ENABLED=false`, en cuyo
caso el sistema funciona de forma completa con el motor determinístico y
los agentes especializados, sin depender de ninguna API externa ni
credencial. Ver `backend/README.md` para el detalle de esta capa y las
variables de entorno asociadas.
