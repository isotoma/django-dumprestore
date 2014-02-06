import zipfile
from unittest import TestCase
from mock import MagicMock, call, patch
from datetime import datetime
from dumprestore import media
import json

fake_media = {
    ".": (["d1", "d2"], ["f1", "f2"]),
    "./d1": (["d3"], ["f3"]),
    "./d2": ([], []),
    "./d1/d3": ([], ["f4"]),
}

class TestFileMetadata(TestCase):
    pass

class TestMediaDriver(TestCase):

    def setUp(self):
        self.archive = MagicMock()
        self.storage = self._storage()
        self.driver = media.MediaDriver(storage=self.storage)

    def _storage(self):
        storage = MagicMock()
        storage.accessed_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.created_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.modified_time = MagicMock(return_value=datetime(2001, 01, 01))
        storage.size = MagicMock(return_value=100)
        storage.listdir=MagicMock(side_effect=lambda x: fake_media[x])
        return storage

    def test_storage_files(self):
        self.storage.listdir.side_effect = [
            (["foo", "bar"], ["x", "y"]),
            ([], ["z"]),
            (["baz"], ["a"]),
            ([], ["b"]),
        ]
        self.assertEqual(sorted(list(self.driver.storage_files())), [
            "bar/a",
            "bar/baz/b",
            "foo/z",
            "x",
            "y",
        ])

    @patch("dumprestore.media.FileMetadata")
    def test_replace_file(self, fmd):
        archive = MagicMock()
        for exists, changed, result in [
            (True, True, True),
            (True, False, False),
            (False, True, True),
            (False, False, True)]:
            self.storage.exists.return_value = exists
            fmd().has_changed.return_value = changed
            rv = self.driver.replace_file("foo", archive)
            self.assertEqual(rv , result, msg="exists=%r changed=%r result=%r" % (exists, changed, result))

    def test_filenames(self):
        self.archive.namelist.return_value = ["x", "y", "data/foo", "data/bar"]
        self.assertEqual(list(self.driver.filenames(self.archive)), ["foo", "bar"])

    @patch('dumprestore.media.settings')
    def test_dump(self, *mocks):
        self.storage.open().__enter__().read.return_value = "data"
        self.driver.dump(self.archive)
        md =  '{"created_time": "2001-01-01T00:00:00", "accessed_time": "2001-01-01T00:00:00", "modified_time": "2001-01-01T00:00:00", "size": 100}'
        self.assertEqual(self.archive.mock_calls, [
            call.writestr('data/f1', "data"),
            call.writestr('meta/f1', md),
            call.writestr('data/f2', "data"),
            call.writestr('meta/f2', md),
            call.writestr('data/d1/f3', "data"),
            call.writestr('meta/d1/f3', md),
            call.writestr('data/d1/d3/f4', "data"),
            call.writestr('meta/d1/d3/f4', md),
            ])

    @patch('tempfile.NamedTemporaryFile')
    def test_before_dump(self, tmp):
        tmp().name = "foo"
        self.driver.before_dump(self.archive)
        self.assertEqual(self.driver.filename, "foo")

    @patch("dumprestore.media.FileMetadata")
    def test_restore(self, fmd):
        self.driver.filenames = MagicMock(return_value=["foo", "bar"])
        self.driver.storage_only = MagicMock(return_value=["baz"])
        fmd().replace_file.return_value = True
        self.assertRaises(media.MediaRestoreException, self.driver.restore, self.archive)
        writer = self.storage.open()
        reader = self.archive.open()
        self.driver.restore(self.archive, True)
        self.assertEqual(writer.mock_calls, [
            call.write(reader.read()),
            call.write(reader.read())
        ])
