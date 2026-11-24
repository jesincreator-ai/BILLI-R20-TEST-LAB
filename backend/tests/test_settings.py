import os
import unittest
from unittest.mock import patch

from billi.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_secret_key_prefers_new_supabase_secret_key(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_new",
            "SUPABASE_SERVICE_ROLE_KEY": "legacy",
        }, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.supabase_secret_key, "sb_secret_new")
        self.assertTrue(settings.supabase_configured)

    def test_missing_cloud_credentials_are_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
        self.assertFalse(settings.supabase_configured)
        self.assertFalse(settings.drive_configured)
        self.assertFalse(settings.gemini_configured)
        self.assertFalse(settings.private_access_configured)


if __name__ == "__main__":
    unittest.main()
