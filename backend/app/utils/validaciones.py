import re
from fastapi import HTTPException, status

def validar_ruc(ruc: str) -> bool:
    """
    Valida que el RUC peruano tenga 11 dígitos numéricos y comience con dígitos válidos (10, 15, 17, 20).
    """
    if not ruc or not isinstance(ruc, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El RUC es obligatorio y debe ser una cadena de texto."
        )
    ruc = ruc.strip()
    if not re.match(r"^\d{11}$", ruc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El RUC debe tener exactamente 11 dígitos numéricos."
        )
    if not (ruc.startswith("10") or ruc.startswith("20") or ruc.startswith("15") or ruc.startswith("17")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El RUC debe iniciar con un prefijo válido (10, 15, 17 o 20)."
        )
    return True

def validar_email(email: str) -> bool:
    """
    Valida el formato de correo electrónico.
    """
    if not email:
        return True
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(patron, email.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formato del correo electrónico no es válido."
        )
    return True

def validar_telefono(telefono: str) -> bool:
    """
    Valida que el teléfono tenga caracteres válidos (dígitos, espacios, guiones, paréntesis o +).
    """
    if not telefono:
        return True
    patron = r"^[\d\+\-\s\(\)]{6,20}$"
    if not re.match(patron, telefono.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El teléfono contiene caracteres no permitidos o longitud incorrecta."
        )
    return True
