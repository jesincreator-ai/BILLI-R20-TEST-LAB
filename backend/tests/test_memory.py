import tempfile
import unittest
from billi.memory import MemoryStore

class MemoryConsentTests(unittest.TestCase):
    def test_consent_required_for_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(tmp + "/memory.db")
            self.assertFalse(store.remember("name", "BILLI", consent=False))
            self.assertIsNone(store.recall("name", consent=True))
            self.assertTrue(store.remember("name", "BILLI", consent=True))
            self.assertEqual(store.recall("name", consent=True), "BILLI")
            self.assertIsNone(store.recall("name", consent=False))

if __name__ == "__main__":
    unittest.main()
