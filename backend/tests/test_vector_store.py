import unittest

from billi.supabase_store import vector_literal


class VectorStoreTests(unittest.TestCase):
    def test_vector_is_serialized_as_pgvector_literal(self):
        self.assertEqual(vector_literal([0.25, -1, 0]), "[0.25,-1,0]")

    def test_empty_embedding_is_rejected(self):
        with self.assertRaises(ValueError):
            vector_literal([])


if __name__ == "__main__":
    unittest.main()
