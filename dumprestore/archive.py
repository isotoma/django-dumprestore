
import zipfile

class Archive:
    
    """ Represents an archive to backup to or restore from.  Just acts as a proxy for zipfile.ZipFile right now. """
    
    def __init__(self, zipfile, prefix=""):
        self.prefix = prefix
        self.zipfile = zipfile
        
    @classmethod
    def new(klass, filename, mode):
        return klass(zipfile.ZipFile(filename, mode, allowZip64=True))
    
    def subarchive(self, prefix):
        if self.prefix:
            newprefix = self.prefix + "/" + prefix
        else:
            newprefix = prefix
        return self.__class__(self.zipfile, newprefix)
    
    def _name(self, name):
        if self.prefix == "":
            return name
        else:
            return self.prefix + "/" + name
    
    def writestr(self, name, data):
        self.zipfile.writestr(self._name(name), data)
        
    def write(self, filename, arcname):
        self.writestr(arcname, open(filename).read())
        
    def namelist(self):
        for n in self.zipfile.namelist():
            if n.startswith(self.prefix):
                yield n[len(self.prefix)+1:]
                
    def open(self, name, *a, **kw):
        return self.zipfile.open(self._name(name), *a, **kw)
            
        
