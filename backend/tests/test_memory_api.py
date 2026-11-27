import os
import tempfile
import unittest

from billi.api import ChatRequest, MemoryRecallRequest, MemoryRememberRequest, chat, health, memory_recall, memory_remember
from fastapi import HTTPException


class MemoryApiTests(unittest.TestCase):
    def setUp(self):
        self.old = {k: os.environ.get(k) for k in ("BILLI_ADMIN_TOKEN", "BILLI_MEMORY_DB")}

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_memory_requires_consent(self):
        os.environ["BILLI_ADMIN_TOKEN"] = "secret"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["BILLI_MEMORY_DB"] = os.path.join(tmp, "memory.db")
            result = memory_remember(MemoryRememberRequest(key="name", value="Jesin", consent=False), "Bearer secret")
            self.assertEqual(result["status"], "not_stored")
            self.assertEqual(memory_recall(MemoryRecallRequest(key="name", consent=True), "Bearer secret")["value"], None)

    def test_memory_round_trip_after_consent(self):
        os.environ["BILLI_ADMIN_TOKEN"] = "secret"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["BILLI_MEMORY_DB"] = os.path.join(tmp, "memory.db")
            stored = memory_remember(MemoryRememberRequest(key="name", value="Jesin", consent=True), "Bearer secret")
            self.assertEqual(stored["status"], "stored")
            recalled = memory_recall(MemoryRecallRequest(key="name", consent=True), "Bearer secret")
            self.assertEqual(recalled["value"], "Jesin")

    def test_chat_memory_requires_consent(self):
        os.environ["BILLI_ADMIN_TOKEN"] = "secret"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["BILLI_MEMORY_DB"] = os.path.join(tmp, "memory.db")
            result = chat(ChatRequest(message="remember this", remember_key="x", remember_value="y", memory_consent=False), "Bearer secret")
            self.assertEqual(result.memory["status"], "not_stored")


if __name__ == "__main__":
    unittest.main()
