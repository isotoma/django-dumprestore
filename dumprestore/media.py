
import os
import zipfile
import tempfile
import logging
import json

from django.core.files import storage as files_storage
from django.conf import settings

from . import registry
from .backupset import BackupDriver

logger = logging.getLogger("dumprestore")

class MediaBackupException(Exception):
    pass

class MediaRestoreException(Exception):
    pass

class FileMetadata:

    """ We store all the metadata we've got, just in case. """

    datums = ['accessed_time', 'created_time', 'modified_time', 'size']

    def __init__(self, storage):
        self.storage = storage

    def _json(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError

    def to_json(self, arcname):
        d = {}
        for m in self.datums:
            d[m] = getattr(self.storage, m)(arcname)
        return json.dumps(d, default=self._json)

    def has_changed(self, arcname, metadata):
        """ Returns True if the file has changed since it was stored. """
        modified = self.storage.modified_time(arcname).isoformat()
        size = self.storage.size(arcname)
        d = json.loads(metadata)
        if modified < d['modified_time'] or size != d['size']:
            return True
        return False

class MediaDriver(BackupDriver):

    """ Knows how to back up from the storage interface. """

    def __init__(self, tempdir="/var/tmp", storage=None):
        self.tempdir = tempdir
        self.storage = storage
        if self.storage is None:
            self.storage = files_storage.get_storage_class()()

    def storage_files(self):
        """ Return a generator of all files in the storage, by walking storage.listdir """
        directories = ["."]
        while directories:
            d = directories.pop(0)
            new_dirs, files = self.storage.listdir(d)
            for nd in new_dirs:
                directories.append(os.path.join(d, nd))
            for f in files:
                arcname = os.path.join(d, f).lstrip("./")
                yield arcname

    def replace_file(self, name, archive):
        """ returns True if a file in the storage is different from the one
        in the archive, by testing the dates and size. """
        replace = False
        meta = FileMetadata(self.storage)
        if self.storage.exists(name):
            metadata = archive.open("meta/%s" % (name,)).read()
            if meta.has_changed(name, metadata):
                logging.debug("Metadata changed for %r" % name)
                replace = True
            else:
                replace = False
        else:
            logging.debug("File does not exist %r" % name)
            replace = True
        return replace

    def storage_only(self, names):
        """ find files that are only present in the storage """
        for f in self.storage_files():
            if f not in names:
                yield f

    def filenames(self, archive):
        """ Return the list of filenames in our zip. This knows that the files are in a media directory. """
        for n in archive.namelist():
            if n.startswith("data/"):
                yield n[len("data/"):]

    def before_dump(self, archive):
        """ Called on all drivers before dumping. """
        f = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=False)
        f.close()
        self.filename = f.name
        logger.debug("Will create temporary file %r" % self.filename)

    def dump(self, archive):
        logger.info("Dumping media")
        count = 0
        meta = FileMetadata(self.storage)
        for arcname in self.storage_files():
            with self.storage.open(arcname) as f:
                archive.writestr("data/%s" % (arcname,), f.read())
            archive.writestr("meta/%s" % (arcname,), meta.to_json(arcname))
            count = count + 1
        logger.info("%d files written" % count)

    def restore(self, archive, force=False):
        names = set(self.filenames(archive))
        storage_only = list(self.storage_only(names))
        if storage_only and not force:
            raise MediaRestoreException("Files present in storage that are not in the backup", storage_only)
        meta = FileMetadata(self.storage)
        for n in names:
            if self.replace_file(n, archive):
                logging.info("Writing %r" % n)
                data = archive.open("data/%s" % (n,)).read()
                self.storage.open(n, "w").write(data)
