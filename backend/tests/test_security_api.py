import unittest

from billi.security import token_matches


class PrivateKnowledgeAccessTests(unittest.TestCase):
    def test_missing_token_never_authorizes(self):
        self.assertFalse(token_matches(None, 'private-test-token'))
        self.assertFalse(token_matches('', 'private-test-token'))

    def test_unconfigured_server_token_fails_closed(self):
        self.assertFalse(token_matches('some-token', None))
        self.assertFalse(token_matches('some-token', ''))


if __name__ == '__main__':
    unittest.main()