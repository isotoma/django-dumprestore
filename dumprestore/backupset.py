
""" A backup set orchestrates collections of backups """

import logging

logger = logging.getLogger("dumprestore")

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

    def __init__(self, name="master", driver=None):
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
        logger.info("%s performing pre-dump checks" % self.name)
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
