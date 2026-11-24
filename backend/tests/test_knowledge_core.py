import unittest

from billi.chunking import chunk_text
from billi.language import detect_language, normalize_language
from billi.security import token_matches
from billi.extractors import extract_text


class LanguageTests(unittest.TestCase):
    def test_detects_english_tamil_and_sinhala(self):
        self.assertEqual(detect_language('Hello BILLI'), 'en')
        self.assertEqual(detect_language('வணக்கம் நண்பா'), 'ta')
        self.assertEqual(detect_language('ආයුබෝවන්'), 'si')

    def test_normalize_auto_and_invalid_language(self):
        self.assertEqual(normalize_language('auto', 'வணக்கம்'), 'ta')
        self.assertEqual(normalize_language('xx', 'Hello'), 'en')


class ChunkingTests(unittest.TestCase):
    def test_chunks_respect_target_and_overlap(self):
        text = 'A' * 1200
        chunks = chunk_text(text, chunk_size=500, overlap=80)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(item) <= 500 for item in chunks))
        self.assertEqual(chunks[0][-80:], chunks[1][:80])

    def test_empty_text_has_no_chunks(self):
        self.assertEqual(chunk_text('   '), [])


class SecurityTests(unittest.TestCase):
    def test_admin_token_matches_only_when_configured(self):
        self.assertTrue(token_matches('a-long-secret', 'a-long-secret'))
        self.assertFalse(token_matches('wrong', 'a-long-secret'))
        self.assertFalse(token_matches(None, 'a-long-secret'))
        self.assertFalse(token_matches('a-long-secret', None))


class ExtractionTests(unittest.TestCase):
    def test_plain_text_and_markdown_are_preserved(self):
        self.assertIn('BILLI knowledge', extract_text(b'BILLI knowledge', 'text/plain', 'note.txt'))
        self.assertIn('# BILLI', extract_text(b'# BILLI', 'text/markdown', 'note.md'))

    def test_html_removes_tags_and_script_content(self):
        source = b'<html><body><h1>BILLI</h1><script>do_not_index()</script><p>Robot knowledge</p></body></html>'
        text = extract_text(source, 'text/html', 'page.html')
        self.assertIn('Robot knowledge', text)
        self.assertNotIn('do_not_index', text)


if __name__ == '__main__':
    unittest.main()