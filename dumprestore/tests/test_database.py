from unittest import TestCase
from mock import MagicMock, call, patch

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


class TestPostgres(TestCase):

    def setUp(self):
        self.driver = database.Postgres()

    @patch("dumprestore.database.subprocess")
    @patch("dumprestore.database.settings")
    def test_dump(self, settings, subprocess):
        settings.DATABASES = DATABASES
        self.driver.dump("/var/tmp/foo", "test")
        self.assertEqual(subprocess.check_call.mock_calls, [
            call(stdargs + [
                  '-U', 'xxuserxx',
                  '-h', 'xxhostxx',
                  '-p', 'xxportxx',
                  'xxnamexx']
                 , env = {'PGPASSWORD': 'xxpasswordxx'})
        ])

    @patch("dumprestore.database.subprocess")
    @patch("dumprestore.database.settings")
    def test_dump_nouser(self, settings, subprocess):
        settings.DATABASES = DATABASES.copy()
        settings.DATABASES['test']['USER'] = None
        self.driver.dump("/var/tmp/foo", "test")
        self.assertEqual(subprocess.check_call.mock_calls, [
            call(stdargs + [
                  '-h', 'xxhostxx',
                  '-p', 'xxportxx',
                  'xxnamexx'
                ], env = {'PGPASSWORD': 'xxpasswordxx'})
        ])

class TestDatabaseDriver(TestCase):

    def setUp(self):
        self.p = patch("dumprestore.database.settings")
        self.settings = self.p.start()
        self.settings.DATABASES = {
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
        self.driver = database.DatabaseDriver()
        self.archive = MagicMock()

    def tearDown(self):
        self.p.stop()

    def test_get_databases_no_order(self):
        self.assertEqual(len(list(self.driver.get_databases())), 3)

    def test_get_databases_ordered(self):
        self.settings.DATABASE_BACKUP_ORDER = ['two']
        databases = list(self.driver.get_databases())
        self.assertEqual(len(databases), 3)
        self.assertEqual(databases[0][0], 'two')
        self.assert_('one' in [x[0] for x in databases])
        self.assert_('three' in [x[0] for x in databases])

    @patch("tempfile.NamedTemporaryFile")
    @patch("dumprestore.database.os")
    def test_dump(self, os, ntf):
        d = MagicMock()
        self.driver.databases = [("one", d)]
        self.driver.dump(self.archive)
        self.assertEqual(d.dump.mock_calls, [call(ntf().name, 'one')])
