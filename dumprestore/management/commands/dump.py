from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from dumprestore.archive import Archive
from dumprestore.default import default_set
from dumprestore import archive

from logging import getLogger

logger = getLogger("dumprestore")

class Command(BaseCommand):
    args = '<filename>'
    help = "Backup to the specified zip filename"

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: backup dump <filename>")
        archive_filename = args[0]
        if hasattr(settings, "DUMPRESTORE_SET"):
            s = settings.DUMPRESTORE_SET
            logger.debug("Using backup set %r configured in settings" % s)
        else:
            logger.debug("Using default backup set")
            s = default_set()
        logger.info("Creating archive at %s" % archive_filename)
        s.archive = Archive.new(archive_filename, "w")
        if not s.before_dump():
            raise SystemExit()
        s.dump()
        s.after_dump()
