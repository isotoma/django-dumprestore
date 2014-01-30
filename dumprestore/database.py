
import os
import subprocess
import logging
import tempfile

from django.conf import settings

from . import registry
from .backupset import BackupDriver

logger = logging.getLogger("dumprestore")

class DatabaseBackupException(Exception):
    pass

databases = {}

class Postgres:
    
    backup_command = ['pg_dump', '-Fc', '-C', '-EUTF-8', '-b', '-o']

    def backup(self, filename, db):
        logger.info("Backing up postgres database %r to %r" % (db, filename))
        conf = settings.DATABASES[db]
        environment = {}
        command = self.backup_command[:]
        command.extend(['-f', filename])
        if conf['USER'] is not None:
            command.extend(['-U', conf['USER']])
        if conf['PASSWORD'] is not None:
            environment['PGPASSWORD'] = conf['PASSWORD']
        if conf['HOST'] is not None:
            command.extend(['-h', conf['HOST']])
        if conf['PORT'] is not None:
            command.extend(['-p', conf['PORT']])
        if conf['NAME'] is not None:
            command.append(conf['NAME'])
        logger.debug("Executing %r" % " ".join(command))
        subprocess.check_call(command, env=environment)
        
databases['django.db.backends.postgresql_psycopg2'] = Postgres
    
class DatabaseDriver(BackupDriver):

    def __init__(self, tempdir="/var/tmp"):
        self.tempdir = tempdir
        self.databases = []
        order = getattr(settings, 'DATABASE_BACKUP_ORDER', ())
        remaining = settings.DATABASES.keys()
        for o in order:
            remaining.remove(o)
        for db in list(order) + list(remaining):
            engine = settings.DATABASES[db]['ENGINE']
            driver = databases.get(engine, None)
            if driver is None:
                raise DatabaseBackupException("No driver for engine %r" % engine)
            self.databases.append((db, driver()))

    def preflight(self):
        print "Backing up the following databases:"
        for db, driver in self.databases:
            print "    %s (%s)" % (db, driver.__class__.__name__)

    def dump(self, archive):
        for db, driver in self.databases:
            logger.info("Backing up database %r" % db)
            f = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=False)
            f.close()
            filename = f.name
            logger.debug("Writing to temporary file %r" % filename)
            driver.backup(filename, db)
            archive.write(filename, "%s.dmp" % (db,))
            logger.debug("Removing temporary file %r" % filename)
            os.unlink(filename)

    def restore(self, archive):
        pass