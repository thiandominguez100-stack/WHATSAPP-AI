"""Start the local-only WA-Bridge AI development server."""
from __future__ import annotations

import ipaddress
import os
import sys

from backend.app import create_app


def server_settings() -> tuple[str, int]:
    host = os.getenv("HOST", "127.0.0.1").strip().lower()
    if host == "localhost":
        host = "127.0.0.1"
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError
    except ValueError:
        raise ValueError(
            "HOST debe ser una dirección de loopback (127.0.0.1 o ::1). "
            "WA-Bridge AI no admite conexiones de red."
        ) from None

    raw_port = os.getenv("PORT", "5000").strip()
    try:
        port = int(raw_port)
    except ValueError:
        raise ValueError("PORT debe ser un número entero entre 1 y 65535.") from None
    if not 1 <= port <= 65535:
        raise ValueError("PORT debe estar entre 1 y 65535.")
    return host, port


app = create_app()

if __name__ == "__main__":
    try:
        host, port = server_settings()
    except ValueError as exc:
        print(f"Configuración no válida: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"WA-Bridge AI disponible solo en este equipo: http://localhost:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
