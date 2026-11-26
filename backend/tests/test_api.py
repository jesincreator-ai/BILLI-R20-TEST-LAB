import os
import tempfile
import unittest

from billi.api import ChatRequest, SearchRequest, chat, health, knowledge_search
from fastapi import HTTPException


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self._old_db = os.environ.get("BILLI_KNOWLEDGE_DB")
        self._old_token = os.environ.get("BILLI_ADMIN_TOKEN")

    def tearDown(self):
        for key, value in (("BILLI_KNOWLEDGE_DB", self._old_db), ("BILLI_ADMIN_TOKEN", self._old_token)):
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_health_reports_truthful_unconfigured_state(self):
        os.environ.pop("BILLI_KNOWLEDGE_DB", None)
        payload = health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["ai_provider"], "not_configured")
        self.assertEqual(payload["database"], "not_configured")

    def test_chat_returns_structured_deterministic_response(self):
        os.environ.pop("BILLI_KNOWLEDGE_DB", None)
        result = chat(ChatRequest(message="hello BILLI"))
        self.assertEqual(result.intent, "greeting")
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertEqual(result.provider, "demo-router")
        self.assertIn("deterministic demo", result.response)

    def test_search_requires_token_and_configured_store(self):
        os.environ["BILLI_ADMIN_TOKEN"] = "secret"
        os.environ.pop("BILLI_KNOWLEDGE_DB", None)
        with self.assertRaises(HTTPException) as ctx:
            knowledge_search(SearchRequest(query="battery"), "Bearer secret")
        self.assertEqual(ctx.exception.status_code, 503)

    def test_search_reads_local_sqlite_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["BILLI_ADMIN_TOKEN"] = "secret"
            os.environ["BILLI_KNOWLEDGE_DB"] = os.path.join(tmp, "knowledge.db")
            from billi.knowledge import KnowledgeDocument, KnowledgeStore

            store = KnowledgeStore(os.environ["BILLI_KNOWLEDGE_DB"])
            store.upsert(KnowledgeDocument("en-1", "Battery", "BILLI battery lasts six hours.", "en"))
            store.close()
            result = knowledge_search(SearchRequest(query="battery"), "Bearer secret")
            self.assertEqual(result["results"][0]["doc_id"], "en-1")
            self.assertEqual(result["source"], "local_sqlite_fts5")


if __name__ == "__main__":
    unittest.main()
