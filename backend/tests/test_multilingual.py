import unittest

from billi.language import choose_language
from billi.api import ChatRequest, chat

class MultilingualResponseTests(unittest.TestCase):
    def test_script_detection(self):
        self.assertEqual(choose_language(None, "வணக்கம்"), "ta")
        self.assertEqual(choose_language(None, "ආයුබෝවන්"), "si")
        self.assertEqual(choose_language(None, "hello"), "en")

    def test_explicit_language_composition(self):
        result = chat(ChatRequest(message="hello", response_language="ta"))
        self.assertEqual(result.intent, "greeting")
        self.assertIn("வணக்கம்", result.response)

    def test_invalid_language_is_rejected(self):
        with self.assertRaises(Exception):
            chat(ChatRequest(message="hello", response_language="xx"))

if __name__ == "__main__":
    unittest.main()
