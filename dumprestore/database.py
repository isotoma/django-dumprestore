
import subprocess
import logging
import tempfile

from django.conf import settings

from . import registry
from . import backup

logger = logging.getLogger("dumprestore")

class DatabaseBackupException(Exception):
    pass

class DatabaseDriverType(registry.DriverRegistry):
    pass

class DatabaseBackupDriver(object):
    __metaclass__ = DatabaseDriverType
    engine = None

class PostgresBackupDriver(DatabaseBackupDriver):
    engine = 'django.db.backends.postgresql_psycopg2'
    
    command = ['pg_dump', '-Fc', '-C', '-EUTF-8', '-b', '-o']
    
    def backup(self, filename, db):
        logger.info("Backing up postgres database %r to %r" % (db, filename))
        conf = settings.DATABASES[db]
        environment = {}
        command = self.command[:]
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

class DatabaseBackupSet(backup.BackupSet):
    
    """ Backup Sets form a tree of backup sets, where the children are backed up in order once the parent backup has completed. """
    
    def __init__(self, destdir="/var/tmp"):
        self.destdir = destdir
        self.drivers = []
        self.databases = []
        self.setup()

    def get_driver(self, engine):
        return DatabaseDriverType.drivers.get(engine, None)
 
    def setup(self):
        order = getattr(settings, 'DATABASE_BACKUP_ORDER', ())
        remaining = settings.DATABASES.keys()
        for o in order:
            remaining.remove(o)
        for db in list(order) + list(remaining):
            engine = settings.DATABASES[db]['ENGINE']
            driver = self.get_driver(engine)
            if driver is None:
                raise DatabaseBackupException("No driver for engine %r" % engine)
            self.databases.append((db, driver()))
    
    def preflight(self):
        print "Backing up the following databases:"
        for db, driver in self.databases:
            print "    %s (%s)" % (db, driver.__class__.__name__)
            
    def backup(self):
        files = []
        for db, driver in self.databases:
            f = tempfile.NamedTemporaryFile(dir=self.destdir, delete=False)
            f.close()
            filename = f.name
            driver.backup(filename, db)
            files.append(("database/%s.dmp" % db, filename))
        return files
    
    def cleanup(self):
        return []
            
        
    