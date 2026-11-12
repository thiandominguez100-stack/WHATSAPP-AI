"""Safe WhatsApp hand-off helpers.

This module only creates official click-to-chat links. It does not control
WhatsApp Web, read private chats, or send messages in the background.
"""
from __future__ import annotations

from urllib.parse import quote

from .security import clean_text, normalize_phone


def build_whatsapp_link(phone: str, message: str) -> str:
    normalized = normalize_phone(phone)
    body = clean_text(message, max_length=2000)
    return f"https://wa.me/{normalized}?text={quote(body, safe='')}"
