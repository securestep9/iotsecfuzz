import ctypes
import inspect
import re
import threading
from binascii import unhexlify
from queue import Queue


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
