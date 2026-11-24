import unittest

from billi.api import ChatRequest, chat, health


class ApiIntegrationTests(unittest.TestCase):
    def test_health_reports_truthful_unconfigured_state(self):
        payload = health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["ai_provider"], "not_configured")
        self.assertEqual(payload["database"], "not_configured")

    def test_chat_returns_structured_deterministic_response(self):
        result = chat(ChatRequest(message="hello BILLI"))
        self.assertEqual(result.intent, "greeting")
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertEqual(result.provider, "demo-router")
        self.assertIn("deterministic demo", result.response)


if __name__ == "__main__":
    unittest.main()
