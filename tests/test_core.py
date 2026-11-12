"""Regression and security tests for WA-Bridge AI."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from backend.agent import _find_contact
from backend.ai_provider import _endpoint, interpret_with_provider
from backend.app import create_app
from backend.database import db_session, database_path
from backend.security import clean_text, normalize_phone
from backend.whatsapp import build_whatsapp_link
from scripts import backup_db


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_env = {
            key: os.environ.get(key)
            for key in ("WA_BRIDGE_DB", "AI_BASE_URL", "AI_MODEL", "AI_API_KEY")
        }
        os.environ["WA_BRIDGE_DB"] = os.path.join(self.temp_dir.name, "test.db")
        os.environ["AI_BASE_URL"] = ""
        os.environ["AI_MODEL"] = ""
        os.environ["AI_API_KEY"] = ""
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        for key, value in self.previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp_dir.cleanup()

    def add_contact(self, name="Ana", phone="+54 9 351 123 4567"):
        return self.client.post("/api/contacts", json={"name": name, "phone": phone})

    def test_empty_database_environment_uses_default_path(self):
        with patch.dict(os.environ, {"WA_BRIDGE_DB": ""}), patch(
            "backend.database.PROJECT_ROOT", Path(self.temp_dir.name)
        ):
            path = database_path()
        self.assertEqual(path, Path(self.temp_dir.name) / "data" / "wa_bridge.db")

    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("+54 9 351 123-4567"), "5493511234567")
        self.assertEqual(normalize_phone("(549) 351.123.4567"), "5493511234567")

    def test_reject_invalid_phone_values(self):
        for value in ("123", "abc5493511234567", "54+93511234567", "", "+"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_phone(value)

    def test_clean_text_rejects_non_text_empty_and_oversized(self):
        for value in (None, 12, "", "   ", "x" * 6):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                clean_text(value, max_length=5)

    def test_whatsapp_link_encodes_message(self):
        url = build_whatsapp_link("5493511234567", "Hola, ¿cómo estás?")
        self.assertTrue(url.startswith("https://wa.me/5493511234567?text="))
        self.assertIn("%C2%BF", url)

    def test_add_contact_and_prepare_draft(self):
        created = self.add_contact()
        self.assertEqual(created.status_code, 201)
        response = self.client.post(
            "/api/chat",
            json={"message": "prepara un mensaje para Ana diciendo que mañana llego a las 10"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["kind"], "draft")
        self.assertEqual(data["draft"]["recipient_name"], "Ana")
        self.assertIn("wa.me/5493511234567", data["draft"]["url"])
        drafts = self.client.get("/api/drafts").get_json()["drafts"]
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["message"], "mañana llego a las 10")

    def test_duplicate_phone_is_rejected(self):
        self.assertEqual(self.add_contact().status_code, 201)
        response = self.add_contact("Ana duplicada", "549 351 123 4567")
        self.assertEqual(response.status_code, 409)

    def test_duplicate_contact_names_require_disambiguation(self):
        self.assertEqual(self.add_contact("Alex", "5493511111111").status_code, 201)
        self.assertEqual(self.add_contact("Alex", "5493512222222").status_code, 201)
        response = self.client.post(
            "/api/chat", json={"message": "prepara un mensaje para Alex diciendo hola"}
        )
        self.assertEqual(response.get_json()["kind"], "ambiguous")
        self.assertEqual(self.client.get("/api/drafts").get_json()["drafts"], [])

    def test_contact_matching_is_exact_and_accent_insensitive(self):
        self.add_contact("Ána", "5493511111111")
        with db_session() as connection:
            exact = _find_contact(connection, "ana")
            partial = _find_contact(connection, "an")
        self.assertEqual(len(exact), 1)
        self.assertEqual(partial, [])

    def test_unknown_provider_intent_falls_back_to_local_parser(self):
        self.add_contact()
        with patch("backend.agent.interpret_with_provider", return_value={"intent": "unknown"}):
            response = self.client.post(
                "/api/chat",
                json={"message": "prepara un mensaje para Ana diciendo hola"},
            )
        self.assertEqual(response.get_json()["kind"], "draft")

    def test_reminder_command_without_task_keyword(self):
        response = self.client.post("/api/chat", json={"message": "recordame estudiar inglés"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "task")
        self.assertEqual(response.get_json()["task"]["title"], "estudiar inglés")

    def test_create_task_and_list_tasks(self):
        response = self.client.post(
            "/api/chat", json={"message": "crear tarea estudiar matemática"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "task")
        tasks = self.client.get("/api/tasks").get_json()["tasks"]
        self.assertEqual(tasks[0]["title"], "estudiar matemática")
        self.assertEqual(tasks[0]["status"], "pending")

    def test_task_status_transitions_and_idempotence(self):
        created = self.client.post("/api/tasks", json={"title": "Estudiar"})
        task_id = created.get_json()["task"]["id"]
        first = self.client.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.get_json()["changed"])
        second = self.client.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
        self.assertFalse(second.get_json()["changed"])
        reopened = self.client.patch(f"/api/tasks/{task_id}", json={"status": "pending"})
        self.assertEqual(reopened.get_json()["status"], "pending")
        task = self.client.get("/api/tasks").get_json()["tasks"][0]
        self.assertIsNone(task["completed_at"])

    def test_invalid_task_updates_and_missing_task(self):
        self.assertEqual(self.client.patch("/api/tasks/1", json={"status": "unknown"}).status_code, 400)
        self.assertEqual(self.client.patch("/api/tasks/999", json={"status": "completed"}).status_code, 404)

    def test_task_due_text_validation(self):
        self.assertEqual(
            self.client.post("/api/tasks", json={"title": "Test", "due_text": "x" * 101}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/tasks", json={"title": "Test", "due_text": 123}).status_code,
            400,
        )

    def test_delete_contact_preserves_saved_draft(self):
        self.add_contact()
        draft = self.client.post(
            "/api/chat", json={"message": "prepara un mensaje para Ana diciendo hola"}
        ).get_json()["draft"]
        response = self.client.delete("/api/contacts/1")
        self.assertEqual(response.status_code, 200)
        saved = self.client.get("/api/drafts").get_json()["drafts"]
        self.assertEqual(saved[0]["id"], draft["id"])
        self.assertEqual(saved[0]["recipient_name"], "Ana")

    def test_draft_link_click_is_idempotent_and_does_not_claim_sent(self):
        self.add_contact()
        draft = self.client.post(
            "/api/chat", json={"message": "prepara un mensaje para Ana diciendo hola"}
        ).get_json()["draft"]
        first = self.client.post(f"/api/drafts/{draft['id']}/clicked", json={})
        second = self.client.post(f"/api/drafts/{draft['id']}/clicked", json={})
        self.assertFalse(first.get_json()["message_sent"])
        self.assertEqual(second.status_code, 200)
        history = self.client.get("/api/history").get_json()["history"]
        self.assertEqual(sum(item["action"] == "whatsapp.open" for item in history), 1)

    def test_missing_draft_returns_404(self):
        self.assertEqual(self.client.post("/api/drafts/999/clicked", json={}).status_code, 404)

    def test_reject_invalid_contact_and_chat_payloads(self):
        self.assertEqual(self.client.post("/api/contacts", json={"name": "", "phone": "5493511234567"}).status_code, 400)
        self.assertEqual(self.client.post("/api/chat", json={"message": 123}).status_code, 400)
        self.assertEqual(self.client.post("/api/chat", json={}).status_code, 400)

    def test_reject_oversized_request(self):
        response = self.client.post("/api/chat", json={"message": "x" * 40000})
        self.assertEqual(response.status_code, 413)
        self.assertIn("error", response.get_json())

    def test_health_and_security_headers(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("object-src 'none'", response.headers["Content-Security-Policy"])

    def test_reject_non_local_host(self):
        response = self.client.get("/api/health", headers={"Host": "example.com"})
        self.assertEqual(response.status_code, 403)

    def test_reject_cross_origin_mutation(self):
        response = self.client.post(
            "/api/contacts",
            json={"name": "Ana", "phone": "5493511234567"},
            headers={"Origin": "https://attacker.example"},
        )
        self.assertEqual(response.status_code, 403)

    def test_reject_cross_site_fetch_metadata(self):
        response = self.client.post(
            "/api/contacts",
            json={"name": "Ana", "phone": "5493511234567"},
            headers={"Sec-Fetch-Site": "cross-site"},
        )
        self.assertEqual(response.status_code, 403)

    def test_reject_non_loopback_client(self):
        response = self.client.get(
            "/api/health",
            environ_base={"REMOTE_ADDR": "192.0.2.10"},
        )
        self.assertEqual(response.status_code, 403)

    def test_allow_same_origin_mutation(self):
        response = self.client.post(
            "/api/contacts",
            json={"name": "Ana", "phone": "5493511234567"},
            headers={"Origin": "http://localhost"},
        )
        self.assertEqual(response.status_code, 201)

    def test_provider_endpoint_validation(self):
        self.assertEqual(
            _endpoint("http://127.0.0.1:11434/v1"),
            "http://127.0.0.1:11434/v1/chat/completions",
        )
        self.assertEqual(
            _endpoint("https://api.example/v1/chat/completions"),
            "https://api.example/v1/chat/completions",
        )
        for url in ("http://example.com/v1", "ftp://localhost/path",
                    "https://user:pass@example.com", "https://example.com/?token=x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _endpoint(url)

    def test_invalid_provider_configuration_falls_back_without_crashing(self):
        with patch.dict(os.environ, {"AI_BASE_URL": "ftp://bad-host", "AI_MODEL": "test"}):
            self.assertIsNone(interpret_with_provider("hola"))

    def test_settings_report_local_ollama(self):
        with patch.dict(os.environ, {
            "AI_BASE_URL": "http://127.0.0.1:11434/v1",
            "AI_MODEL": "qwen2.5:1.5b",
            "AI_API_KEY": "ollama",
        }):
            settings = self.client.get("/api/settings").get_json()
        self.assertEqual(settings["provider_mode"], "ollama_local")
        self.assertTrue(settings["provider_is_local"])
        self.assertEqual(settings["model"], "qwen2.5:1.5b")



    def test_settings_survive_malformed_provider_url(self):
        with patch.dict(os.environ, {
            "AI_BASE_URL": "http://[malformed",
            "AI_MODEL": "test",
        }):
            response = self.client.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["provider_is_local"])
        self.assertFalse(response.get_json()["provider_configured"])

    def test_backup_creates_integrity_checked_copy(self):
        backup_root = Path(self.temp_dir.name) / "project"
        backup_root.mkdir()
        with patch.object(backup_db, "ROOT", backup_root):
            result = backup_db.main()
        self.assertEqual(result, 0)
        backup_files = list((backup_root / "backups").glob("wa_bridge_*.db"))
        self.assertEqual(len(backup_files), 1)
        with closing(sqlite3.connect(backup_files[0])) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertTrue({"contacts", "drafts", "tasks", "history"}.issubset(tables))

if __name__ == "__main__":
    unittest.main()
