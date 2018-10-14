from functools import reduce, wraps

__all__ = ["EventEmitter"]


def once(func):
    func.__once = True
    return func


class EventEmitter:

    def __init__(self):
        self.__listeners = dict()

    def append_listener(self, name, func):
        if name not in self.__listeners:
            self.__listeners[name] = list()
        self.__listeners[name].append(func)

    def prepend_listener(self, name, func):
        if name not in self.__listeners:
            self.__listeners[name] = list()
        self.__listeners[name].insert(0, func)

    def append_once_listener(self, name, func):
        @once
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        if name not in self.__listeners:
            self.__listeners[name] = list()
        self.__listeners[name].append(wrapper)

    def prepend_once_listener(self, name, func):
        @once
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        if name not in self.__listeners:
            self.__listeners[name] = list()
        self.__listeners[name].insert(0, wrapper)

    def on(self, name, func):
        self.append_listener(name, func)

    def once(self, name, func):
        self.append_once_listener(name, func)

    def emit(self, name, *args, **kwargs):
        to_remove = list()
        for index, listener in enumerate(self.__listeners[name]):
            listener(*args, **kwargs)
            if hasattr(listener, "__once"):
                to_remove.append(index)
        self.__listeners[name] = [value for index, value in
                                  enumerate(self.__listeners[name]) if
                                  index not in to_remove]

    def event_names(self):
        return self.__listeners.keys()

    def listeners_number(self):
        return reduce(lambda acc, elem: acc + len(elem),
                      self.__listeners.values(), list())

    def listeners(self, name):
        return self.__listeners[name]

    def all_listeners(self):
        return reduce(lambda acc, elem: acc + [elem],
                      self.__listeners.values(), list())

    def remove_listener(self, name, func):
        if func in self.__listeners[name]:
            self.__listeners[name].remove(func)

    def remove_listeners(self, name):
        self.__listeners.pop(name, None)

    def remove_all_listeners(self):
        self.__listeners.clear()
