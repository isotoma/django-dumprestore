from .database import DatabaseDriver
from .media import MediaDriver
from .backupset import BackupSet

def default_set():
    s = BackupSet()
    s.addChild(BackupSet("media", MediaDriver()))
    s.addChild(BackupSet("database", DatabaseDriver()))
    return s
