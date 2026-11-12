"""Flask application and HTTP API."""
from __future__ import annotations

import ipaddress
import os
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request

from .agent import handle_message
from .ai_provider import _endpoint
from .database import db_session, init_db
from .security import clean_text, normalize_phone


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _body() -> dict[str, Any]:
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def _is_loopback_address(value: str | None) -> bool:
    if not value:
        return False
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _is_local_host(value: str) -> bool:
    try:
        host = urlsplit("//" + value).hostname
    except ValueError:
        return False
    return bool(host and host.lower() in _LOCAL_HOSTS)


def _same_origin(origin: str, host_url: str) -> bool:
    try:
        supplied = urlsplit(origin)
        expected = urlsplit(host_url)
        return (
            supplied.scheme in {"http", "https"}
            and supplied.scheme == expected.scheme
            and supplied.hostname == expected.hostname
            and supplied.port == expected.port
            and supplied.username is None
            and supplied.password is None
        )
    except ValueError:
        return False


def create_app() -> Flask:
    load_dotenv(PROJECT_ROOT / ".env")
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

    init_db()

    @app.before_request
    def enforce_local_access():
        # This app has no login system; it must remain reachable only from this PC.
        if not _is_local_host(request.host):
            abort(403, description="WA-Bridge AI solo acepta conexiones locales.")
        if not _is_loopback_address(request.remote_addr):
            abort(403, description="Conexión remota bloqueada.")
        if request.method in _MUTATING_METHODS:
            fetch_site = request.headers.get("Sec-Fetch-Site")
            if fetch_site and fetch_site not in {"same-origin", "none"}:
                abort(403, description="Solicitud de otro sitio bloqueada.")
            origin = request.headers.get("Origin")
            if origin and not _same_origin(origin, request.host_url):
                abort(403, description="Solicitud de otro origen bloqueada.")

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'; object-src 'none'"
        )
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        with db_session() as connection:
            connection.execute("SELECT 1").fetchone()
        return jsonify({"ok": True, "app": "WA-Bridge AI", "mode": "local"})

    @app.post("/api/chat")
    def chat():
        body = _body()
        try:
            message = clean_text(body.get("message"), max_length=1500)
            with db_session() as connection:
                result = handle_message(connection, message)
            return jsonify(result)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/contacts")
    def get_contacts():
        with db_session() as connection:
            rows = connection.execute(
                "SELECT id, name, phone, created_at FROM contacts ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return jsonify({"contacts": [dict(row) for row in rows]})

    @app.post("/api/contacts")
    def add_contact():
        body = _body()
        try:
            name = clean_text(body.get("name"), max_length=100)
            phone = normalize_phone(body.get("phone"))
            with db_session() as connection:
                cursor = connection.execute(
                    "INSERT INTO contacts(name, phone) VALUES (?, ?)", (name, phone)
                )
                connection.execute(
                    "INSERT INTO history(action, summary) VALUES (?, ?)",
                    ("contact.create", f"Contacto agregado: {name}"),
                )
                row = connection.execute(
                    "SELECT id, name, phone, created_at FROM contacts WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
                connection.commit()
            return jsonify({"contact": dict(row)}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except sqlite3.IntegrityError:
            return jsonify({"error": "Ese número ya está registrado."}), 409

    @app.delete("/api/contacts/<int:contact_id>")
    def delete_contact(contact_id: int):
        with db_session() as connection:
            row = connection.execute(
                "SELECT name FROM contacts WHERE id = ?", (contact_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "Contacto no encontrado."}), 404
            connection.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            connection.execute(
                "INSERT INTO history(action, summary) VALUES (?, ?)",
                ("contact.delete", f"Contacto eliminado: {row['name']}"),
            )
            connection.commit()
        return jsonify({"ok": True})

    @app.get("/api/tasks")
    def get_tasks():
        with db_session() as connection:
            rows = connection.execute(
                """SELECT id, title, due_text, status, created_at, completed_at
                   FROM tasks ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,
                   id DESC LIMIT 200"""
            ).fetchall()
        return jsonify({"tasks": [dict(row) for row in rows]})

    @app.post("/api/tasks")
    def add_task():
        body = _body()
        try:
            title = clean_text(body.get("title"), max_length=300)
            due_text_raw = body.get("due_text", "")
            if not isinstance(due_text_raw, str):
                raise ValueError("La fecha debe ser texto.")
            due_text = due_text_raw.strip()
            if len(due_text) > 100:
                raise ValueError("La fecha o nota no puede superar 100 caracteres.")
            with db_session() as connection:
                cursor = connection.execute(
                    "INSERT INTO tasks(title, due_text) VALUES (?, ?)", (title, due_text)
                )
                connection.execute(
                    "INSERT INTO history(action, summary) VALUES (?, ?)",
                    ("task.create", f"Tarea creada: {title}"),
                )
                row = connection.execute(
                    "SELECT id, title, due_text, status, created_at FROM tasks WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
                connection.commit()
            return jsonify({"task": dict(row)}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        body = _body()
        status = body.get("status")
        if status not in {"pending", "completed"}:
            return jsonify({"error": "Estado no válido."}), 400
        with db_session() as connection:
            row = connection.execute(
                "SELECT title, status FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "Tarea no encontrada."}), 404
            if row["status"] == status:
                return jsonify({"ok": True, "status": status, "changed": False})
            connection.execute(
                """UPDATE tasks SET status = ?,
                   completed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
                   WHERE id = ?""",
                (status, status, task_id),
            )
            connection.execute(
                "INSERT INTO history(action, summary) VALUES (?, ?)",
                ("task.update", f"Tarea actualizada: {row['title']} → {status}"),
            )
            connection.commit()
        return jsonify({"ok": True, "status": status, "changed": True})

    @app.get("/api/drafts")
    def get_drafts():
        with db_session() as connection:
            rows = connection.execute(
                """SELECT id, recipient_name, phone, message, status, created_at
                   FROM drafts ORDER BY id DESC LIMIT 100"""
            ).fetchall()
        return jsonify({"drafts": [dict(row) for row in rows]})

    @app.get("/api/history")
    def get_history():
        with db_session() as connection:
            rows = connection.execute(
                "SELECT id, action, summary, status, created_at FROM history "
                "ORDER BY id DESC LIMIT 100"
            ).fetchall()
        return jsonify({"history": [dict(row) for row in rows]})

    @app.post("/api/drafts/<int:draft_id>/clicked")
    def mark_draft_opened(draft_id: int):
        with db_session() as connection:
            row = connection.execute(
                "SELECT recipient_name, status FROM drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "Borrador no encontrado."}), 404
            if row["status"] != "link_clicked":
                connection.execute(
                    "UPDATE drafts SET status = 'link_clicked' WHERE id = ?", (draft_id,)
                )
                connection.execute(
                    "INSERT INTO history(action, summary, status) VALUES (?, ?, ?)",
                    ("whatsapp.open", f"Se solicitó abrir el enlace de WhatsApp para {row['recipient_name']}; envío no verificado.",
                     "opened"),
                )
                connection.commit()
        return jsonify({"ok": True, "status": "link_clicked",
                        "message_sent": False})

    @app.get("/api/tools")
    def get_tools():
        from .tools import public_tool_catalog
        return jsonify({"tools": public_tool_catalog()})

    @app.get("/api/settings")
    def settings():
        base_url = os.getenv("AI_BASE_URL", "").strip()
        model = os.getenv("AI_MODEL", "").strip()
        provider_is_local = False
        endpoint_valid = False
        if base_url:
            try:
                _endpoint(base_url)
                endpoint_valid = True
                parsed = urlsplit(base_url)
                provider_is_local = bool(
                    parsed.scheme == "http"
                    and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
                )
            except ValueError:
                endpoint_valid = False
        provider_configured = bool(endpoint_valid and model)
        return jsonify({
            "provider_configured": provider_configured,
            "provider_mode": "ollama_local" if provider_configured and provider_is_local else (
                "compatible_api" if provider_configured else "local_parser"
            ),
            "provider_is_local": provider_is_local,
            "model": model if provider_configured else None,
            "api_key_present": bool(os.getenv("AI_API_KEY", "").strip()),
        })

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "La solicitud es demasiado grande."}), 413

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": getattr(error, "description", "Acceso bloqueado.")}), 403

    return app
