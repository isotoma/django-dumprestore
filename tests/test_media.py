import zipfile
from unittest import TestCase
from mock import MagicMock, call, patch

from dumprestore import media

fake_media = {
    ".": (["d1", "d2"], ["f1", "f2"]),
    "./d1": (["d3"], ["f3"]),
    "./d2": ([], []),
    "./d1/d3": ([], ["f4"]),
}

class TestFileBackupDriver(TestCase):
    
    @patch('dumprestore.media.zipfile.ZipFile')
    @patch('dumprestore.media.settings')
    @patch('dumprestore.media.storage.get_storage_class')
    def test_backup(self, *mocks):
        driver = media.FileBackupDriver()
        storage_class = MagicMock()
        storage = storage_class()
        storage.listdir=MagicMock(side_effect=lambda x: fake_media[x])
        media.storage.get_storage_class.return_value = storage_class
        zf = media.zipfile.ZipFile()
        media.settings.MEDIA_ROOT="/baz"
        driver.backup("/foo/bar")
        self.assertEqual(zf.mock_calls, [
            call.write('/baz/f1', 'f1'),
            call.write('/baz/f2', 'f2'),
            call.write('/baz/d1/f3', 'd1/f3'),
            call.write('/baz/d1/d3/f4', 'd1/d3/f4'),
            call.close(),
            ])
        
class TestMediaBackupSet(TestCase):
    
    def test_get_driver(self):
        s = media.MediaBackupSet()
        self.assertEqual(s.get_driver('django.core.files.storage.FileSystemStorage'),
                         media.FileBackupDriver)

    
    @patch('dumprestore.media.storage.get_storage_class')
    def test_preflight(self, *mocks):
        s = media.MediaBackupSet()
        storage_class = MagicMock()
        storage = storage_class()
        media.storage.get_storage_class.return_value = storage_class
        storage_class.__module__ = "django.core.files.storage"
        storage_class.__name__ = "FileSystemStorage"
        s.preflight()
        self.assertEqual(s.driver.__class__, media.FileBackupDriver)

    @patch('dumprestore.media.tempfile.NamedTemporaryFile')
    def test_backup(self, *mocks):
        tmp = media.tempfile.NamedTemporaryFile()
        tmp.name = "xxfooxx"
        s = media.MediaBackupSet()
        s.driver = MagicMock()
        self.assertEqual(s.backup(), [("media.zip", "xxfooxx")])
        self.assertEqual(s.driver.mock_calls, [call.backup("xxfooxx")])
        