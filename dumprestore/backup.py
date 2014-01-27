import os
import sys
import itertools
import zipfile
import tempfile
import subprocess
import logging

from django.conf import settings
from django.core.files.storage import get_storage_class

from . import registry

logger = logging.getLogger("backup")

class BackupSet:
    
    def __init__(self, destdir="/var/tmp"):
        self.destdir = destdir
        self.parent = None
        self.children = []
        
    def setSetParent(self, parent):
        self.parent = parent
        parent.children.append(self)
        
    def preflight(self):
        """ Perform pre-flight checks. Return True if they passed, or False if they failed. """
        checks = []
        for c in self.children:
            checks.append(c.preflight())
        for c in checks:
            if not c:
                return False
        return True
    
    def backup(self):
        """ Backup source data to temporary files, and return the names of the files. """
        files = []
        for c in self.children:
            files.extend(c.backup())
        return files
    
    def cleanup(self):
        """ Produce a list of files to delete once everything has succeeded. """
        files = []
        for c in self.children:
            files.append(c.cleanup())
        return files
    
class RootBackupSet(BackupSet):
    
    def __init__(self, filename):
        self.filename = filename
        BackupSet.__init__(self)
    
    def backup(self):
        files = BackupSet.backup(self)
        z = zipfile.ZipFile(self.filename, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True)
        for name, path in files:
            z.write(path, name)
        z.close()
        print "Root Backup Set Written to", self.filename
        
    def cleanup(self):
        files = BackupSet.cleanup(self)
        print "Deleting files", files
        
    
    