"""Input validation and security helpers."""
from __future__ import annotations

import re


def clean_text(value: object, *, max_length: int = 500) -> str:
    if not isinstance(value, str):
        raise ValueError("Se esperaba texto.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("El texto no puede estar vacío.")
    if len(cleaned) > max_length:
        raise ValueError(f"El texto supera el máximo de {max_length} caracteres.")
    return cleaned


def normalize_phone(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("El teléfono debe ser texto.")
    # wa.me expects an international number without +, spaces, or punctuation.
    digits = re.sub(r"[^0-9]", "", value)
    if not 8 <= len(digits) <= 15:
        raise ValueError(
            "Usa el número internacional completo, con código de país, "
            "entre 8 y 15 dígitos."
        )
    return digits
