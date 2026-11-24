import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from billi.api import app, health


class ApiIntegrationTests(unittest.TestCase):
    def test_health_reports_true_connection_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            payload = health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"], "not_configured")
        self.assertEqual(payload["drive"], "not_configured")
        self.assertEqual(payload["private_access"], "not_configured")

    def test_private_chat_rejects_requests_without_configured_admin_token(self):
        with patch.dict(os.environ, {}, clear=True):
            client = TestClient(app)
            response = client.post("/api/chat", json={"message": "hello"})
        self.assertEqual(response.status_code, 503)

    def test_private_chat_rejects_incorrect_admin_token(self):
        with patch.dict(os.environ, {"BILLI_ADMIN_TOKEN": "correct-long-token"}, clear=True):
            client = TestClient(app)
            response = client.post(
                "/api/chat",
                headers={"X-BILLI-ADMIN-TOKEN": "wrong-token"},
                json={"message": "hello"},
            )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
