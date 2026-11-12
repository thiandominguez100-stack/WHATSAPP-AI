"""Input validation and security helpers."""
from __future__ import annotations

import re


_ALLOWED_PHONE_CHARS = re.compile(r"^\+?[0-9\s().-]+$")


def clean_text(value: object, *, max_length: int = 500) -> str:
    if not isinstance(value, str):
        raise ValueError("Se esperaba texto.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("El texto no puede estar vacío.")
    if len(cleaned) > max_length:
        raise ValueError(f"El texto supera el máximo de {max_length} caracteres.")
    if any(ord(char) < 32 and char not in "\n\t" for char in cleaned):
        raise ValueError("El texto contiene caracteres de control no permitidos.")
    return cleaned


def normalize_phone(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("El teléfono debe ser texto.")
    raw = value.strip()
    if not raw or not _ALLOWED_PHONE_CHARS.fullmatch(raw):
        raise ValueError(
            "El teléfono solo puede contener dígitos, un + inicial, espacios, "
            "paréntesis, puntos o guiones."
        )
    if "+" in raw[1:]:
        raise ValueError("El signo + solo puede aparecer al principio.")
    digits = re.sub(r"[^0-9]", "", raw)
    if not 8 <= len(digits) <= 15:
        raise ValueError(
            "Usa el número internacional completo, con código de país, "
            "entre 8 y 15 dígitos."
        )
    return digits
