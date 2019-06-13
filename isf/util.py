import ctypes
import inspect
import re
import threading
from binascii import unhexlify
from queue import Queue
import os
import sys
import site


class MacAddress:

    def __init__(self, value):
        if isinstance(value, MacAddress):
            self.value = value.value
            return
        elif not isinstance(value, str):
            raise ValueError('Invalid MAC address format')
        if re.match('[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$',
                    value.lower()):
            self.value = value
        else:
            raise ValueError('Invalid MAC address format')

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
            raise ValueError('Invalid IPv4 address format')
        if re.match(
                '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}'
                + '([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$',
                value.lower()):
            self.value = value
        else:
            raise ValueError('Invalid IPv4 address format')

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class CallbackIterator:
    """
    Transform a function that takes a callback into generator.
    Source: https://stackoverflow.com/a/9969000
    """

    def __init__(self, func, *, args=None, kwargs=None,
                 callback_name='callback'):
        """
        Create new generator from function that takes callback & its arguments.

        :param func: function that takes a callback
        :param args: arguments array to be passed to function
        :param kwargs: keyword arguments dict to be passed to function
        :param callback_name: name of the callback keyword argument
        """
        self.func = func
        self.queue = Queue(maxsize=1)
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}
        self.sentinel = object()
        self.callback_name = callback_name

        def callback(value):
            self.queue.put(value)

        def run():
            if self.callback_name in inspect.getfullargspec(self.func).args:
                result = self.func(*self.args, **self.kwargs,
                                   **{self.callback_name: callback})
            else:
                result = self.func(*self.args, **self.kwargs)
            if result:
                self.queue.put(result)
            self.queue.put(self.sentinel)

        self.thread = threading.Thread(target=run)
        self.thread.start()

    def __iter__(self):
        return self

    def __next__(self):
        obj = self.queue.get(True, None)
        if obj is self.sentinel:
            raise StopIteration
        else:
            return obj


def async_raise(thread_obj, exception):
    target_tid = thread_obj.ident
    if target_tid not in {thread.ident for thread in threading.enumerate()}:
        raise ValueError('Invalid thread object')

    affected_count = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(target_tid), ctypes.py_object(exception))

    if affected_count == 0:
        raise ValueError('Invalid thread identity')
    elif affected_count > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid),
                                                   ctypes.c_long(0))
        raise SystemError('PyThreadState_SetAsyncExc failed')


def activate_virtualenv(bin_dir):
    """
    Activates virtual environment for current process.
    Reference:
    https://github.com/pypa/virtualenv/blob/master/virtualenv_embedded/activate_this.py
    :param bin_dir: Binaries directory of virtual environment
    :return:
    """
    os.environ['PATH'] = os.pathsep.join(
        [bin_dir] + os.environ.get('PATH', '').split(os.pathsep))

    base = os.path.dirname(bin_dir)

    # Virtual env is right above bin directory
    os.environ['VIRTUAL_ENV'] = base

    # Add the virtual environments site-package
    is_pypy = hasattr(sys, 'pypy_version_info')
    is_jython = sys.platform.startswith('java')
    if is_jython:
        site_packages = os.path.join(base, 'Lib', 'site-packages')
    elif is_pypy:
        site_packages = os.path.join(base, 'site-packages')
    else:
        is_win = sys.platform == 'win32'
        if is_win:
            site_packages = os.path.join(base, 'Lib', 'site-packages')
        else:
            site_packages = os.path.join(base, 'lib',
                                         'python{}'.format(sys.version[:3]),
                                         'site-packages')

    prev = set(sys.path)
    site.addsitedir(site_packages)
    sys.real_prefix = sys.prefix
    sys.prefix = base

    # Move the added items to the front of the path, in place
    new = list(sys.path)
    sys.path[:] = [i for i in new if i not in prev] + [i for i in new if
                                                       i in prev]
