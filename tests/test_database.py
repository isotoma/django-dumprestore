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
        