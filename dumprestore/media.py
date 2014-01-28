
import os
import zipfile
import tempfile
import logging
import json

from django.core.files import storage
from django.conf import settings

from . import registry
from .backupset import BackupSet

logger = logging.getLogger("dumprestore")

class MediaBackupException(Exception):
    pass

class MediaDriverType(registry.DriverRegistry):
    pass

class MediaBackupDriver(object):
    __metaclass__ = MediaDriverType
    engine = None

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
        modified = self.storage.modified_time(arcname)
        size = self.storage.size(arcname)
        d = json.loads(metadata)
        if modified != d['modified_time'] or size != d['size']:
            return True
        return False
        
class FileBackupDriver(MediaBackupDriver):
    """ Implements backups of the default FileSystemStorage """
    engine = 'django.core.files.storage.FileSystemStorage'
    
    def storage_files(self, storage):
        directories = ["."]
        files = []
        while directories:
            d = directories.pop()
            new_dirs, files = storage.listdir(d)
            for nd in new_dirs:
                directories.append(os.path.join(d, nd))
            for f in files:
                arcname = os.path.join(d, f).lstrip("./")
                yield arcname
    
    def backup(self, filename):
        st = storage.get_storage_class()()
        z = zipfile.ZipFile(filename, mode="w", allowZip64=True)
        count = 0
        meta = FileMetadata(st)
        for arcname in self.storage_files(st):
            f = st.open(arcname)
            z.writestr("media/%s" % arcname, f.read())
            z.writestr("meta/%s" % arcname, meta.to_json(arcname))
            f.close()
            count = count + 1
        z.close()
        logger.info("%d files written" % count)
        
    def restore(self, filename):
        st = storage.get_storage_class()()
        z = zipfile.ZipFile(filename, mode="r", allowZip64=True)
        
        
        

class MediaBackupSet(BackupSet):
    
    def __init__(self, destdir="/var/tmp"):
        self.driver = None
        self.filename = None
        self.destdir = destdir
        
    def get_driver(self, engine):
        return MediaDriverType.drivers.get(engine, None)
        
    def preflight(self):
        cls = storage.get_storage_class()
        fqcn = cls.__module__ + "." + cls.__name__
        driver = self.get_driver(fqcn)
        if driver is None:
            raise MediaBackupException("No driver for engine %r" % engine)
        self.driver = driver()
        logger.info("Backup media with %r" % self.driver.__class__.__name__)
        f = tempfile.NamedTemporaryFile(dir=self.destdir, delete=False)
        f.close()
        self.filename = f.name
        logger.debug("Will create temporary file %r" % self.filename)

    def backup(self):
        logger.info("Writing media to %r" % self.filename)
        self.driver.backup(self.filename)
        return [("media.zip", self.filename)]

    def cleanup(self):
        return [self.filename]
    
    