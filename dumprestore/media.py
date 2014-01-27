
import os
import zipfile

from django.core.files import storage
from django.conf import settings

from . import registry
import tempfile
from . import backup
from django.core.files import storage

class MediaBackupException(Exception):
    pass

class MediaDriverType(registry.DriverRegistry):
    pass

class MediaBackupDriver(object):
    __metaclass__ = MediaDriverType
    engine = None

class FileBackupDriver(MediaBackupDriver):
    """ Implements backups of the default FileSystemStorage """
    engine = 'django.core.files.storage.FileSystemStorage'
    
    def backup(self, filename):
        st = storage.get_storage_class()()
        z = zipfile.ZipFile(filename, mode="w", allowZip64=True)
        directories = ["."]
        files = []
        root = settings.MEDIA_ROOT
        count = 0
        while directories:
            d = directories.pop()
            new_dirs, files = st.listdir(d)
            for nd in new_dirs:
                directories.append(os.path.join(d, nd))
            for f in files:
                arcname = os.path.join(d, f)
                source = os.path.join(root, arcname)
                z.write(source, arcname)
                count = count + 1
        z.close()
        print "%d files written" % count

class MediaBackupSet(backup.BackupSet):
    
    def __init__(self, destdir="/var/tmp"):
        self.driver = None
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
        print "Backup media with", self.driver.__class__.__name__

    def backup(self):
        f = tempfile.NamedTemporaryFile(dir=self.destdir, delete=False)
        f.close()
        print "Writing media to", f.name
        self.driver.backup(f.name)
        return [("media.zip", f.name)]

    def cleanup(self):
        return []
    
    