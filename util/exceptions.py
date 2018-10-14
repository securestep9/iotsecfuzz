class InitializationException(Exception):
    pass


class ModuleLoadingException(InitializationException):
    pass


class GuiLoadingException(InitializationException):
    pass


class InvalidStateException(Exception):
    pass


class NoSuchModuleException(Exception):
    pass

