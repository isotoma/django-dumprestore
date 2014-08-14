==================
django-dumprestore
==================

When used properly, it ensures mutable state is dumped coherently - i.e. that
when restored there are no dangling links. Obviously you need to understand what
coherent means, which will vary from application to application.

This application adds two management commands, `dump` and `restore`.

By default these will dump and restore:

 * all databases listed in settings.DATABASES
 * all media accessible via the Storage API

However, you can extend this to provide coherent dumps of any other data you
require.

To use in it's default mode, just add it to your INSTALLED_APPS and it should
"just work".

You do need to understand what "coherent" means for your application. By default
we assume that your database may have links to media files, but not the other
way around.

Because the database is dumped first, it means that if your application
continues to be used during the dump and entries are written to the database
that refer to media files, then we might restore orphan media, but we won't
restore dangling links in the database.

This is considered better.

If you have any other mutable data (files on disk not in media, redis databases
etc.) Then you need to write code to include these in the dump and the restore.
You can see how to do this below.

Example use case
================

There are many approaches to releasing software, but many of them involve
Having a production environment and upgrading it.

When you do this you need some way of safely rolling back to the previous state.

Ideally you could do this without losing data, and without restoring your
database, but this isn't always the case. For many software products it's not
worth the
effort of ensuring this is possible too - a bit of downtime is often acceptable
compared to the cost of avoiding it.

So, django-dumprestore.  This assists in the process of restoring your environment
to an earlier state, often in practice when recovering from a failed release, but this
could also be used to transfer state to the blue part of a blue/greeen deployment
infrastructure, or to move data into a pre-production environment for testing (although
you should always ensure you anonymize data in pre-production environments remember!)

Here's how you could approach a release using django-dumprestore:

 1. Back up your code (for example sudo tar -cjf backup/foo.YYYY-MM-DD.code.tar.bz2 foo)
 2. Back up your data (for example foo/bin/django dump backup/foo.YYYY-MM-DD.data.zip)
 3. Perform the software release
 4. Discover it failed. Decide to roll back
 5. Stop all of the associated processes - web, celery, etc.
 6. Move the existing code directory out of the way (for example mv foo foo.failed.YYYY-MM-DD)
 7. Perhaps take a dump of the database in it's failed state if you want (with pg_dump etc.)
 8. Restore the code directory (sudo tar -jxf backup/foo.YYYY-MM-DD.code.tar.bz2)
 9. Use psql -l to check the databases and their ownership
 10. Drop the affected databases and recreate with correct owners
 11. Restore the data (foo/bin/django restore backup/foo.YYYY-MM-DD.data.zip)
 12. Restart the associated service processes (web, celery etc.)
 13. Check that everything is working
 14. Tidy up (logfiles, other remains of broken deployment, refer back to developers)

Step 9 ensures that data is restored in a coherent manner, and will restore the
media too, even if it is in a remote location such as S3.

Defining your own backup sets
=============================

A "Backup Set" is a collection of backups taken in a specified order. The order is important because this helps you ensure your dump is consistent, even if it is taken while your system is changing.

You can define a backup set in settings.DUMPRESTORE_SET.

For example, in settings.py::

    from dumprestore.backupset import BackupSet
    from dumprestore.media import MediaDriver
    from dumprestore.database import DatabaseDriver

    DUMPRESTORE_SET=BackupSet()
    DUMPRESTORE_SET.addChild(BackupSet("media", MediaDriver()))
    DUMPRESTORE.SET.addChild(BackupSet("database", DatabaseDriver()))

This would give you the default behaviour, to back up the media and then the databases.

If you wanted to add a direct filesystem directory as well::

    from dumprestore.backupset import BackupSet
    from dumprestore.media import MediaDriver
    from dumprestore.filesystem import FilesystemDriver
    from dumprestore.database import DatabaseDriver

    DUMPRESTORE_SET=BackupSet()
    DUMPRESTORE_SET.addChild(BackupSet("media", MediaDriver()))
    DUMPRESTORE.SET.addChild(BackupSet("database", DatabaseDriver()))
    DUMPRESTORE.SET.addChild(BackupSet("foofiles", FilesystemDriver("/var/lib/foo")))

This would also back up /var/lib/foo, after everything else, and allow this to be restored easily.

BackupSets are hierarchical, so you can add children all the way down if required. This allows you to carefully specify ordering and dependencies.

Running the unit tests
======================

Activate a virtual environment.

Then::

    pip install -r requirements.txt
    nose2

