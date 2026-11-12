"""Natural-language command interpreter and safe tool dispatcher."""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from .ai_provider import interpret_with_provider
from .security import clean_text
from .whatsapp import build_whatsapp_link


MESSAGE_PATTERN = re.compile(
    r"^(?:prepara|preparame|redacta|escribe|arma|manda|mandale|envia|enviale)"
    r"\s+(?:un\s+)?mensaje\s+(?:para|a)\s+(.+?)\s+"
    r"(?:diciendole|diciendo(?:le)?(?:\s+que)?|que\s+diga|con\s+el\s+texto)\s+(.+)$",
    re.IGNORECASE,
)
TASK_PATTERN = re.compile(
    r"^(?:crear|crea|agregar|agrega|anotar|anota|recordame|recu[eé]rdame|programa)"
    r"\s+(?:una\s+)?(?:tarea|recordatorio)\s*(?:de|para|:)??\s*(.+)$",
    re.IGNORECASE,
)


def _record(connection: sqlite3.Connection, action: str, summary: str,
            status: str = "ok") -> None:
    connection.execute(
        "INSERT INTO history(action, summary, status) VALUES (?, ?, ?)",
        (action[:80], summary[:500], status[:30]),
    )


def _local_intent(text: str) -> dict[str, str]:
    match = MESSAGE_PATTERN.match(text.strip())
    if match:
        return {
            "intent": "draft_message",
            "recipient": match.group(1).strip(" .,:;"),
            "message": match.group(2).strip(),
        }

    match = TASK_PATTERN.match(text.strip())
    if match:
        title = match.group(1).strip(" .,:;")
        if title:
            return {"intent": "create_task", "title": title, "due_text": ""}

    normalized = text.strip().casefold()
    if any(term in normalized for term in ("mostrar contactos", "listar contactos",
                                            "ver contactos", "mis contactos")):
        return {"intent": "list_contacts"}
    if any(term in normalized for term in ("mostrar tareas", "listar tareas",
                                            "ver tareas", "mis tareas")):
        return {"intent": "list_tasks"}
    if normalized in {"ayuda", "help", "que puedes hacer", "qué puedes hacer"}:
        return {"intent": "help"}
    return {"intent": "unknown"}


def _find_contact(connection: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    rows = connection.execute(
        "SELECT id, name, phone FROM contacts ORDER BY name COLLATE NOCASE"
    ).fetchall()
    query = name.strip().casefold()
    exact = [row for row in rows if row["name"].casefold() == query]
    if exact:
        return exact
    return [
        row for row in rows
        if query in row["name"].casefold() or row["name"].casefold() in query
    ]


def handle_message(connection: sqlite3.Connection, user_text: str) -> dict[str, Any]:
    """Interpret a user request; only dispatch allow-listed, low-risk operations."""
    text = clean_text(user_text, max_length=1500)
    intent = interpret_with_provider(text) or _local_intent(text)
    kind = intent.get("intent", "unknown")

    if kind == "draft_message":
        recipient = str(intent.get("recipient", "")).strip()
        message = str(intent.get("message", "")).strip()
        if not recipient or not message or len(message) > 2000:
            return {
                "reply": "No pude identificar con suficiente claridad el destinatario y el texto. "
                         "Probá: «prepara un mensaje para Ana diciendo que llego a las 10».",
                "kind": "clarification",
            }

        matches = _find_contact(connection, recipient)
        if not matches:
            _record(connection, "message.lookup", f"No se encontró el contacto: {recipient}", "not_found")
            connection.commit()
            return {
                "reply": f"No encontré a «{recipient}» en tus contactos. Agregalo primero en Contactos.",
                "kind": "not_found",
            }
        if len(matches) > 1:
            names = ", ".join(row["name"] for row in matches[:5])
            return {
                "reply": f"Encontré varios contactos que coinciden: {names}. "
                         "Escribí el nombre completo para evitar elegir a la persona equivocada.",
                "kind": "ambiguous",
            }

        contact = matches[0]
        link = build_whatsapp_link(contact["phone"], message)
        cursor = connection.execute(
            """INSERT INTO drafts(contact_id, recipient_name, phone, message)
               VALUES (?, ?, ?, ?)""",
            (contact["id"], contact["name"], contact["phone"], message),
        )
        draft_id = cursor.lastrowid
        _record(connection, "whatsapp.prepare",
                f"Borrador preparado para {contact['name']}; requiere revisión manual.")
        connection.commit()
        return {
            "reply": f"Preparé un borrador para {contact['name']}. Revisá el texto y el destinatario; "
                     "WhatsApp se abrirá para que decidas si lo enviás.",
            "kind": "draft",
            "draft": {
                "id": draft_id,
                "recipient_name": contact["name"],
                "phone": contact["phone"],
                "message": message,
                "url": link,
            },
        }

    if kind == "create_task":
        title = str(intent.get("title", "")).strip()
        due_text = str(intent.get("due_text", "")).strip()[:100]
        if not title:
            return {"reply": "Decime qué tarea querés guardar.", "kind": "clarification"}
        title = clean_text(title, max_length=300)
        cursor = connection.execute(
            "INSERT INTO tasks(title, due_text) VALUES (?, ?)", (title, due_text)
        )
        _record(connection, "task.create", f"Tarea creada: {title}")
        connection.commit()
        return {
            "reply": f"Guardé la tarea: «{title}»."
                     + (f" Fecha indicada: {due_text}." if due_text else ""),
            "kind": "task",
            "task": {"id": cursor.lastrowid, "title": title, "due_text": due_text,
                     "status": "pending"},
        }

    if kind == "list_contacts":
        rows = connection.execute(
            "SELECT name, phone FROM contacts ORDER BY name COLLATE NOCASE LIMIT 30"
        ).fetchall()
        if not rows:
            return {"reply": "Todavía no hay contactos guardados.", "kind": "contacts"}
        entries = [f"{row['name']} ({row['phone']})" for row in rows]
        return {"reply": "Contactos guardados:\n" + "\n".join(entries), "kind": "contacts"}

    if kind == "list_tasks":
        rows = connection.execute(
            "SELECT id, title, due_text, status FROM tasks "
            "WHERE status = 'pending' ORDER BY id DESC LIMIT 20"
        ).fetchall()
        if not rows:
            return {"reply": "No tenés tareas pendientes.", "kind": "tasks"}
        entries = [
            f"#{row['id']} {row['title']}" + (f" — {row['due_text']}" if row["due_text"] else "")
            for row in rows
        ]
        return {"reply": "Tareas pendientes:\n" + "\n".join(entries), "kind": "tasks"}

    return {
        "reply": (
            "Puedo ayudarte a preparar mensajes, guardar tareas y consultar contactos o tareas.\n"
            "Ejemplos:\n"
            "• prepara un mensaje para Ana diciendo que mañana llego a las 10\n"
            "• crear tarea estudiar matemática\n"
            "• mostrar contactos\n"
            "• mostrar tareas"
        ),
        "kind": "help",
    }
