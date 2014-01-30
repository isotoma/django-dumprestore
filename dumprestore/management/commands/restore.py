from django.core.management.base import BaseCommand, CommandError
from dumprestore.backupset import Archive
from dumprestore.default import default_set

class Command(BaseCommand):
    args = '<filename>'
    help = "Backup to the specified zip filename"
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: restore <filename>")
        s = default_set()
        s.archive = Archive(args[0], "r")
        if not s.before_restore():
            raise SystemExit()
        s.restore()
        s.after_restore()
    