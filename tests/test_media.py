import zipfile
from unittest import TestCase
from mock import MagicMock, call, patch
from datetime import datetime
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
        storage.accessed_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.created_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.modified_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.size = MagicMock(return_value=100)
        storage.listdir=MagicMock(side_effect=lambda x: fake_media[x])
        media.storage.get_storage_class.return_value = storage_class
        zf = media.zipfile.ZipFile()
        media.settings.MEDIA_ROOT="/baz"
        driver.backup("/foo/bar")
        read = storage.open().read()
        data = '{"created_time": "2001-01-01T00:00:00", "accessed_time": "2001-01-01T00:00:00", "modified_time": "2001-01-01T00:00:00", "size": 100}'
        self.assertEqual(zf.mock_calls, [
            call.writestr('media/f1', read),
            call.writestr('meta/f1', data),
            call.writestr('media/f2', read),
            call.writestr('meta/f2', data),
            call.writestr('media/d1/f3', read),
            call.writestr('meta/d1/f3', data),
            call.writestr('media/d1/d3/f4', read),
            call.writestr('meta/d1/d3/f4', data),
            call.close(),
            ])
        
class TestMediaBackupSet(TestCase):
    
    def test_get_driver(self):
        s = media.MediaBackupSet()
        self.assertEqual(s.get_driver('django.core.files.storage.FileSystemStorage'),
                         media.FileBackupDriver)

    
    def _storage(self):
        storage_class = MagicMock()
        media.storage.get_storage_class.return_value = storage_class
        storage = media.storage.get_storage_class()
        storage_class.__module__ = "django.core.files.storage"
        storage_class.__name__ = "FileSystemStorage"
        return storage
        
    @patch('dumprestore.media.storage.get_storage_class')
    def test_preflight(self, *mocks):
        self._storage()
        s = media.MediaBackupSet()
        s.preflight()
        self.assertEqual(s.driver.__class__, media.FileBackupDriver)

    @patch('dumprestore.media.storage.get_storage_class')
    @patch('dumprestore.media.tempfile.NamedTemporaryFile')
    def test_backup(self, *mocks):
        storage = self._storage()
        tmp = media.tempfile.NamedTemporaryFile()
        tmp.name = "xxfooxx"
        s = media.MediaBackupSet()
        s.preflight()
        s.driver = MagicMock()
        self.assertEqual(s.backup(), [("media.zip", "xxfooxx")])
        self.assertEqual(s.driver.mock_calls, [call.backup("xxfooxx")])
        
    @patch('dumprestore.media.storage.get_storage_class')
    @patch('dumprestore.media.tempfile.NamedTemporaryFile')
    def test_cleanup(self, *mocks):
        self._storage()
        tmp = media.tempfile.NamedTemporaryFile()
        tmp.name = "xxfooxx"
        s = media.MediaBackupSet()
        s.preflight()
        s.driver = MagicMock()
        self.assertEqual(s.backup(), [("media.zip", "xxfooxx")])
        self.assertEqual(s.driver.mock_calls, [call.backup("xxfooxx")])
        self.assertEqual(s.cleanup(), ["xxfooxx"])
    
    def test_restore(self, *mocks):
        storage = self._storage()
        s = media.MediaBackupSet()
        s.preflight()
        