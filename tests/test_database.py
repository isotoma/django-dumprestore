from unittest import TestCase
from mock import MagicMock, call

from dumprestore import database


DATABASES = {
    'test': {
        'USER': 'xxuserxx',
        'PASSWORD': 'xxpasswordxx',
        'HOST': 'xxhostxx',
        'PORT': 'xxportxx',
        'NAME': 'xxnamexx',
    }
}

stdargs = ['pg_dump', '-Fc', '-C', '-EUTF-8', '-b', '-o', '-f', '/var/tmp/foo']

 
class TestPostgresBackupDriver(TestCase):
    
    def setUp(self):
        database.settings = settings = MagicMock()
        database.subprocess = MagicMock()
        database.subprocess.check_call = MagicMock()
    
    def test_backup(self):
        database.settings.DATABASES = DATABASES
        driver = database.PostgresBackupDriver()
        driver.backup("/var/tmp/foo", "test")
        self.assertEqual(database.subprocess.check_call.mock_calls, [
            call(stdargs + [
                  '-U', 'xxuserxx',
                  '-h', 'xxhostxx',
                  '-p', 'xxportxx',
                  'xxnamexx']
                 , env = {'PGPASSWORD': 'xxpasswordxx'})
        ])
        
    def test_backup_nouser(self):
        database.settings.DATABASES = DATABASES
        database.settings.DATABASES['test']['USER'] = None
        driver = database.PostgresBackupDriver()
        driver.backup("/var/tmp/foo", "test")
        self.assertEqual(database.subprocess.check_call.mock_calls, [
            call(stdargs + [
                  '-h', 'xxhostxx',
                  '-p', 'xxportxx',
                  'xxnamexx'
                ], env = {'PGPASSWORD': 'xxpasswordxx'})
        ])
 
class TestDatabaseBackupSet(TestCase):
    
    def setUp(self):
        database.settings = settings = MagicMock()
        database.settings.DATABASES = {
            'one': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                },
            'two': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                },
            'three': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
            }
        }
     
    def test_setup_no_order(self):
        s = database.DatabaseBackupSet()
        self.assertEqual(len(s.databases), 3)
        
    def test_setup_order(self):
        database.settings.DATABASE_BACKUP_ORDER = ['two']
        s = database.DatabaseBackupSet()
        self.assertEqual(len(s.databases), 3)
        self.assertEqual(s.databases[0][0], 'two')
        self.assert_('one' in [x[0] for x in s.databases])
        self.assert_('three' in [x[0] for x in s.databases])
        
    def test_backup(self):
        ntf = MagicMock()
        database.tempfile.NamedTemporaryFile = ntf
        s = database.DatabaseBackupSet()
        driver = MagicMock()
        s.databases = [
            ('one', driver)]
        s.backup()
        self.assertEqual(driver.backup.mock_calls, [call(ntf().name, 'one')])
        