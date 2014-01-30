from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dumprestore.archive import Archive
from dumprestore.default import default_set
from dumprestore import archive

class Command(BaseCommand):
    args = '<filename>'
    help = "Backup to the specified zip filename"
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: restore <filename>")
        if hasattr(settings, "DUMPRESTORE_SET"):
            s = settings.DUMPRESTORE_SET
        else:
            s = default_set()
        s.archive = archive.Archive.new(args[0], "r")
        if not s.before_restore():
            raise SystemExit()
        s.restore()
        s.after_restore()
    