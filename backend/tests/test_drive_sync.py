import unittest

from billi.drive import file_version
from billi.drive_sync import needs_reindex


class DriveVersionTests(unittest.TestCase):
    def test_unchanged_drive_file_is_not_reindexed(self):
        metadata = {
            "id": "drive-1",
            "name": "facts.txt",
            "mimeType": "text/plain",
            "modifiedTime": "2026-11-24T10:00:00Z",
            "size": "12",
            "md5Checksum": "same-checksum",
        }
        existing = {"version_key": file_version(metadata), "status": "indexed"}
        self.assertFalse(needs_reindex(existing, metadata))

    def test_changed_drive_file_is_reindexed(self):
        old = {"version_key": "old-checksum", "status": "indexed"}
        new = {"id": "drive-1", "md5Checksum": "new-checksum"}
        self.assertTrue(needs_reindex(old, new))

    def test_same_version_skip_is_not_retried_on_every_sync(self):
        metadata = {"id": "drive-1", "md5Checksum": "unsupported-format"}
        existing = {"version_key": file_version(metadata), "status": "skipped"}
        self.assertFalse(needs_reindex(existing, metadata))


if __name__ == "__main__":
    unittest.main()
