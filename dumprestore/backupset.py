import os
import sys
import zipfile
import logging

logger = logging.getLogger("backup")

class Archive:
    
    """ Represents an archive to backup to or restore from.  Just acts as a proxy for zipfile.ZipFile right now. """
    
    def __init__(self, zipfile, prefix=""):
        self.prefix = prefix
        self.zipfile = zipfile
        
    @classmethod
    def new(klass, filename, mode):
        return klass(zipfile.ZipFile(filename, mode, allowZip64=True))
    
    def subarchive(self, prefix):
        if self.prefix:
            newprefix = self.prefix + "/" + prefix
        else:
            newprefix = prefix
        return self.__class__(self.zipfile, newprefix)
    
    def _name(self, name):
        if self.prefix == "":
            return name
        else:
            return self.prefix + "/" + name
    
    def writestr(self, name, data):
        self.zipfile.writestr(self._name(name), data)
        
    def write(self, filename, arcname):
        self.writestr(arcname, open(filename).read())
        
    def namelist(self):
        for n in self.zipfile.namelist():
            if n.startswith(self.prefix):
                yield n[len(self.prefix)+1:]
                
    def open(self, name, *a, **kw):
        return self.zipfile.open(self._name(name), *a, **kw)
            
        
class BackupDriver:
    
    def before_dump(self, archive):
        """ Check that everything is ok to back up to the specified archive. """
        
    def dump(self, archive):
        """ Perform the dump to the archive. """
        
    def after_dump(self, archive):
        """ Perform cleanup operations. """
        
    def before_restore(self, archive):
        """ Check that everything is ok before a restore """
        
    def restore(self, archive):
        """ Perform the restore """
        
    def after_restore(self, archive):
        """ Perform cleanup operations """
    
class BackupSet:
    
    """ Orchestrates a collection of backups. First performs operations on it's children, then uses it's driver if required """
    
    def __init__(self, name=None, driver=None):
        self.name = name
        self.__archive = None
        self.children = []
        self.parent = None
        self.driver = driver
        
    def addChild(self, child):
        child.parent = self
        self.children.append(child)
        
    def _get_archive(self):
        if self.__archive is None:
            return self.parent.archive.subarchive(self.name)
        else:
            return self.__archive
        
    def _set_archive(self, archive):
        self.__archive = archive
        
    archive = property(_get_archive, _set_archive)
        
    def before_dump(self):
        """ Perform pre-flight checks. Return True if they passed, or False if they failed. """
        checks = []
        for c in self.children:
            checks.append(c.before_dump())
        if self.driver is not None:
            checks.append(self.driver.before_dump(self.archive))
        return False not in checks
    
    def dump(self):
        """ Backup source data to temporary files, and return the names of the files. """
        for c in self.children:
            c.dump()
        if self.driver is not None:
            self.driver.dump(self.archive)
    
    def after_dump(self):
        """ Perform cleanup operations """
        for c in self.children:
            c.after_dump()
        if self.driver is not None:
            self.driver.after_dump(self.archive)
            
    def before_restore(self):
        """ Perform any checks required before restoring, return True on success, False on failure. """
        checks = []
        for c in self.children:
            checks.append(c.before_restore())
        if self.driver is not None:
            checks.append(self.driver.before_restore(self.archive))
        return False not in checks
    
    def restore(self):
        for c in self.children:
            c.restore()
        if self.driver is not None:
            self.driver.restore(self.archive)
    
    def after_restore(self):
        """ Perform cleanup operations """
        for c in self.children:
            c.after_restore()
        if self.driver is not None:
            self.driver.after_restore(self.archive)