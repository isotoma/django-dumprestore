==================
django-dumprestore
==================

This is an extensible framework for performing dumps and restores of volatile data for Django applications.

This application adds two management commands, dump and restore.

By default these will dump and restore:

 * all databases listed in settings.DATABASES
 * all media accessible via the Storage API

However, you can extend this to provide coherent dumps of any other data you require.

To use in it's default mode, just add it to your INSTALLED_APPS and it should "just work"

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

