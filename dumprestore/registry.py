
import abc

class DriverRegistry(abc.ABCMeta):
    drivers = {}
    
    def __new__(meta, class_name, bases, new_attrs):
        cls = super(DriverRegistry, meta).__new__(
            meta, class_name, bases, new_attrs)
        if cls.engine is not None:
            DriverRegistry.drivers[cls.engine] = cls
        return cls
    
