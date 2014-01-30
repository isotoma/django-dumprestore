import os
import sys
import zipfile
import logging

logger = logging.getLogger("backup")

class Archive:
    
    """ Represents an archive to backup to or restore from.  Just acts as a proxy for zipfile.ZipFile right now. """
    
    def __init__(self, filename, mode="r"):
        self.zipfile = zipfile.ZipFile(filename, mode, allowZip64=True)
        
    def __getattr__(self, name):
        return getattr(self.zipfile, name)
        
class BackupDriver:
    
    def before_dump(self, archive):
        """ Check that everything is ok to back up to the specified archive. """
        
    def dump(self, prefix, archive):
        """ Perform the dump to the archive. """
        
    def after_dump(self, archive):
        """ Perform cleanup operations. """
        
    def before_restore(self, archive):
        """ Check that everything is ok before a restore """
        
    def restore(self, prefix, archive):
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
            return self.parent.archive
        else:
            return self.__archive
        
    def _set_archive(self, archive):
        self.__archive = archive
        
    archive = property(_get_archive, _set_archive)
        
    def prefix(self):
        assert(not (self.name is None and self.parent is not None))
        if self.name is None:
            prefix = ""
        elif self.parent is not None:
            prefix = self.parent.prefix() + "/" + self.name
            prefix = prefix.lstrip("/")
        else:
            prefix = self.name
        return prefix
    
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
            self.driver.dump(self.prefix(), self.archive)
    
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
            self.driver.restore(self.prefix(), self.archive)
    
    def after_restore(self):
        """ Perform cleanup operations """
        for c in self.children:
            c.after_restore()
        if self.driver is not None:
            self.driver.after_restore(self.archive)