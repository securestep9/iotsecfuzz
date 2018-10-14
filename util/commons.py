import pkgutil
import sys
import inspect


def load_modules_from_directory(dir_name):
    for importer, package_name, is_pkg in pkgutil.walk_packages([dir_name]):
        if package_name not in sys.modules:
            importer.find_module(package_name).load_module(package_name)


def get_owner_class(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[
                          0])
        if isinstance(cls, type):
            return cls
    return None
