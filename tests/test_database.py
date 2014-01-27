from unittest import TestCase
from mock import MagicMock, call

from dumprestore import database

database.settings = settings = MagicMock()
database.subprocess = MagicMock()
database.subprocess.check_call = check_call = MagicMock()

class TestPostgresBackupDriver(TestCase):
    
    def test_backup(self):
        settings.DATABASES = {
            'test': {
                'USER': 'xxuserxx',
                'PASSWORD': 'xxpasswordxx',
                'HOST': 'xxhostxx',
                'PORT': 'xxportxx',
                'NAME': 'xxnamexx',
            }
        }
        driver = database.PostgresBackupDriver()
        driver.backup("/var/tmp/foo", "test")
        self.assertEqual(check_call.mock_calls, [
            call(['pg_dump', '-Fc', '-C', '-EUTF-8', '-b', '-o', 
                  '-f', '/var/tmp/foo',
                  '-U', 'xxuserxx',
                  '-h', 'xxhostxx',
                  '-p', 'xxportxx',
                  'xxnamexx'],
                 env = {'PGPASSWORD': 'xxpasswordxx'},
                 )])
        