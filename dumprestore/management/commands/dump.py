from django.core.management.base import BaseCommand, CommandError
from dumprestore.backupset import Archive
from dumprestore.default import default_set

class Command(BaseCommand):
    args = '<filename>'
    help = "Backup to the specified zip filename"
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: backup <filename>")
        s = default_set()
        s.archive = Archive.new(args[0], "w")
        if not s.before_dump():
            raise SystemExit()
        s.dump()
        s.after_dump()
    