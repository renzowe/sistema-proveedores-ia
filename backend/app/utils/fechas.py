from datetime import datetime, timezone


def ahora_utc() -> datetime:
    """
    Hora actual en UTC, sin zona horaria. Reemplaza a `datetime.utcnow()`
    (obsoleto desde Python 3.12) con el mismo valor: las columnas DateTime
    de los modelos guardan UTC "naive" y así se mantiene el formato existente.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
