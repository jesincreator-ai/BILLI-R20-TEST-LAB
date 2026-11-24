import unittest
from billi.intent import classify

class IntentTests(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(classify("hello BILLI").name, "greeting")
    def test_search(self):
        self.assertEqual(classify("search the knowledge base").name, "knowledge_search")
    def test_status(self):
        self.assertEqual(classify("system status").name, "status")
    def test_unknown(self):
        self.assertEqual(classify("tell me a story").name, "unknown")

if __name__ == "__main__":
    unittest.main()
