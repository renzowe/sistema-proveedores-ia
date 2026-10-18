#!/bin/sh
set -e

# Los datos de ejemplo solo se cargan si se pide explícitamente (docker compose
# local). En producción no se activa, para no mezclar datos de prueba con los
# reales. Ambos scripts son idempotentes: no duplican si los datos ya existen.
if [ "$SEED_DATA" = "true" ]; then
    python -m app.utils.seed_data
    python -m app.utils.seed_historial
fi

# PORT lo define la plataforma (p. ej. Render); en local se usa 8000.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
