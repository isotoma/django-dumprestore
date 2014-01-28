from django.core.management.base import BaseCommand, CommandError
from dumprestore.backupset import RootBackupSet
from dumprestore.database import DatabaseBackupSet
from dumprestore.media import MediaBackupSet

class Command(BaseCommand):
    args = '<filename>'
    help = "Backup to the specified zip filename"
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: restore <filename>")
        s = RootBackupSet(args[0])
        MediaBackupSet().setSetParent(s)
        DatabaseBackupSet().setSetParent(s)
        s.preflight()
        s.restore()
        s.cleanup()
    