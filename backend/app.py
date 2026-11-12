"""Flask application and HTTP API."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from .agent import handle_message
from .database import connect_db, init_db
from .security import clean_text, normalize_phone


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _body() -> dict[str, Any]:
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else {}


def create_app() -> Flask:
    load_dotenv(PROJECT_ROOT / ".env")
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

    init_db()

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        with connect_db() as connection:
            connection.execute("SELECT 1").fetchone()
        return jsonify({"ok": True, "app": "WA-Bridge AI", "mode": "local"})

    @app.post("/api/chat")
    def chat():
        body = _body()
        try:
            message = clean_text(body.get("message"), max_length=1500)
            with connect_db() as connection:
                result = handle_message(connection, message)
            return jsonify(result)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/contacts")
    def get_contacts():
        with connect_db() as connection:
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
            with connect_db() as connection:
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
        with connect_db() as connection:
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
        with connect_db() as connection:
            rows = connection.execute(
                """SELECT id, title, due_text, status, created_at, completed_at
                   FROM tasks ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,
                   id DESC"""
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
            due_text = due_text_raw.strip()[:100]
            with connect_db() as connection:
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
        with connect_db() as connection:
            row = connection.execute(
                "SELECT title FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "Tarea no encontrada."}), 404
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
        return jsonify({"ok": True, "status": status})

    @app.get("/api/history")
    def get_history():
        with connect_db() as connection:
            rows = connection.execute(
                "SELECT id, action, summary, status, created_at FROM history "
                "ORDER BY id DESC LIMIT 100"
            ).fetchall()
        return jsonify({"history": [dict(row) for row in rows]})

    @app.post("/api/drafts/<int:draft_id>/opened")
    def mark_draft_opened(draft_id: int):
        with connect_db() as connection:
            row = connection.execute(
                "SELECT recipient_name FROM drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "Borrador no encontrado."}), 404
            # This means the link was opened, not that a message was sent.
            connection.execute(
                "UPDATE drafts SET status = 'opened_in_whatsapp' WHERE id = ?", (draft_id,)
            )
            connection.execute(
                "INSERT INTO history(action, summary, status) VALUES (?, ?, ?)",
                ("whatsapp.open", f"Se abrió WhatsApp para {row['recipient_name']}; envío no verificado.",
                 "opened"),
            )
            connection.commit()
        return jsonify({"ok": True, "status": "opened_in_whatsapp"})

    @app.get("/api/settings")
    def settings():
        configured = bool(os.getenv("AI_BASE_URL", "").strip() and
                          os.getenv("AI_MODEL", "").strip())
        return jsonify({
            "provider_configured": configured,
            "provider_mode": "compatible_api" if configured else "local_parser",
            "api_key_present": bool(os.getenv("AI_API_KEY", "").strip()),
        })

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "La solicitud es demasiado grande."}), 413

    return app
