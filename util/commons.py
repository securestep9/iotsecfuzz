import pkgutil
import sys
import inspect
import re
import ctypes
import threading
from binascii import unhexlify


class MacAddress:

    def __init__(self, value):
        if isinstance(value, MacAddress):
            self.value = value.value
            return
        elif not isinstance(value, str):
            raise ValueError("Invalid MAC address format")
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                    value.lower()):
            self.value = value
        else:
            raise ValueError("Invalid MAC address format")

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def get_bytes(self):
        return unhexlify(self.value.replace(":", ""))


class IPv4:

    def __init__(self, value):
        if isinstance(value, IPv4):
            self.value = value.value
            return
        elif not isinstance(value, str):
            raise ValueError("Invalid IPv4 address format")
        if re.match(
                "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",
                value.lower()):
            self.value = value
        else:
            raise ValueError("Invalid IPv4 address format")

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


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


def async_raise(thread_obj, exception):
    target_tid = thread_obj.ident
    if target_tid not in {thread.ident for thread in threading.enumerate()}:
        raise ValueError("Invalid thread object")

    affected_count = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(target_tid), ctypes.py_object(exception))

    if affected_count == 0:
        raise ValueError("Invalid thread identity")
    elif affected_count > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid),
                                                   ctypes.c_long(0))
        raise SystemError("PyThreadState_SetAsyncExc failed")
