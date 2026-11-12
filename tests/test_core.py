"""Core tests for WA-Bridge AI."""
from __future__ import annotations

import os
import tempfile
import unittest

from backend.app import create_app
from backend.security import normalize_phone
from backend.whatsapp import build_whatsapp_link


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["WA_BRIDGE_DB"] = os.path.join(self.temp_dir.name, "test.db")
        os.environ.pop("AI_BASE_URL", None)
        os.environ.pop("AI_MODEL", None)
        os.environ.pop("AI_API_KEY", None)
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()
        os.environ.pop("WA_BRIDGE_DB", None)

    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("+54 9 351 123-4567"), "5493511234567")
        with self.assertRaises(ValueError):
            normalize_phone("123")

    def test_whatsapp_link(self):
        url = build_whatsapp_link("5493511234567", "Hola, ¿cómo estás?")
        self.assertTrue(url.startswith("https://wa.me/5493511234567?text="))
        self.assertIn("%C2%BF", url)

    def test_add_contact_and_prepare_draft(self):
        created = self.client.post(
            "/api/contacts",
            json={"name": "Ana", "phone": "+54 9 351 123 4567"},
        )
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

    def test_create_task(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "crear tarea estudiar matemática"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "task")
        tasks = self.client.get("/api/tasks").get_json()["tasks"]
        self.assertEqual(tasks[0]["title"], "estudiar matemática")

    def test_reject_invalid_phone(self):
        response = self.client.post(
            "/api/contacts",
            json={"name": "Persona", "phone": "123"},
        )
        self.assertEqual(response.status_code, 400)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])


if __name__ == "__main__":
    unittest.main()
