import unittest

from billi.knowledge import KnowledgeDocument, KnowledgeStore


class KnowledgeStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = KnowledgeStore()

    def tearDown(self):
        self.store.close()

    def test_upsert_search_and_language_filter(self):
        self.store.bulk_upsert(
            [
                KnowledgeDocument("en-1", "Battery", "BILLI battery lasts six hours.", "en"),
                KnowledgeDocument("ta-1", "பேட்டரி", "பில்லி பேட்டரி ஆறு மணி நேரம்.", "ta"),
            ]
        )
        results = self.store.search("battery", language="en")
        self.assertEqual([item["doc_id"] for item in results], ["en-1"])
        self.assertEqual(results[0]["language"], "en")

    def test_upsert_replaces_searchable_content(self):
        self.store.upsert(KnowledgeDocument("doc", "Old", "old phrase", "en"))
        self.store.upsert(KnowledgeDocument("doc", "New", "new phrase", "en"))
        self.assertEqual(self.store.search("old"), [])
        self.assertEqual(self.store.search("new")[0]["title"], "New")

    def test_jsonl_export_is_utf8_and_metadata_safe(self):
        self.store.upsert(
            KnowledgeDocument("si-1", "සිංහල", "BILLI දත්ත", "si", metadata={"kind": "qa"})
        )
        payload = self.store.export_jsonl()
        self.assertIn("සිංහල", payload)
        self.assertIn('"kind": "qa"', payload)

    def test_rejects_unknown_language(self):
        with self.assertRaises(ValueError):
            self.store.upsert(KnowledgeDocument("x", "x", "x", "fr"))


if __name__ == "__main__":
    unittest.main()
