"""Allow-listed tool catalog exposed to the agent and dashboard.

Adding a tool here documents its intent and side-effect policy. A tool must
also have a validated handler before it can perform an operation.
"""
TOOL_REGISTRY = {
    "contacts.list": {
        "intent": "list_contacts",
        "description": "Consultar los contactos guardados localmente.",
        "side_effect": "none",
        "confirmation_required": False,
    },
    "tasks.list": {
        "intent": "list_tasks",
        "description": "Consultar las tareas pendientes.",
        "side_effect": "none",
        "confirmation_required": False,
    },
    "tasks.create": {
        "intent": "create_task",
        "description": "Guardar una tarea en la base de datos local.",
        "side_effect": "local_write",
        "confirmation_required": False,
    },
    "whatsapp.prepare_message": {
        "intent": "draft_message",
        "description": "Crear un borrador y un enlace oficial de WhatsApp para revisión.",
        "side_effect": "draft_only",
        "confirmation_required": True,
    },
}


def public_tool_catalog() -> list[dict[str, object]]:
    """Return descriptions without exposing implementation details."""
    return [
        {"name": name, **metadata}
        for name, metadata in TOOL_REGISTRY.items()
    ]


def is_allowed_intent(intent: str) -> bool:
    return any(item["intent"] == intent for item in TOOL_REGISTRY.values())
