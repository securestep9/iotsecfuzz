import functools
import sys
from enum import Enum

import core.console.ISFConsole as ISFConsole
import util.commons as commons
from util.events import EventEmitter
from util.exceptions import *


class State(Enum):
    LOADING_MODULES = 0
    LOADING_GUI = 1
    READY = 2


class Param:

    def __init__(self, description, *, value_type=str, required=False,
                 default_value=None):
        self.description = description
        self.default_value = default_value
        self.value_type = value_type
        self.required = required


def get_module_instance(name):
    return loaded_modules[name]() if name in loaded_modules else None


submodule_methods = list()
container_classes = dict()


class ISFContainer:
    def __init__(self, *, version="1.0", author=None):
        if state != State.LOADING_MODULES:
            raise InvalidStateException(("Can only load modules while in %s " +
                                         "state (current state is %s)") % (
                                            State.LOADING_MODULES.name,
                                            state.name))
        self.version = version
        self.author = author

    def __call__(self, cls):
        global container_classes
        if not hasattr(cls, "in_params") or not isinstance(
                cls.in_params, dict):
            raise ModuleLoadingException(("Container '%s' does not " +
                                          "provide input parameters list")
                                         % cls.__name__)
        if cls.__module__.startswith("modules"):
            raise ModuleLoadingException(
                "DO NOT IMPORT ISF MODULES DIRECTLY " +
                "- USE self.get_module_instance(name) INSTEAD")

        class ContainerWrapper(cls, EventEmitter):
            version = self.version
            author = self.author

            def __init__(self, *args, **kwargs):
                self.get_module_instance = get_module_instance
                super(ContainerWrapper, self).__init__(*args, **kwargs)

            def run(self, params):
                validated = validate_params(
                    super(ContainerWrapper, self).in_params, params)
                if validated:
                    out = super(ContainerWrapper, self).run(validated)
                    return out if out else dict()

        container_classes[cls.__module__.replace(".", "/")] = ContainerWrapper
        return ContainerWrapper


def register_submodules():
    for data in submodule_methods:
        register_submodule(data)


def register_submodule(data):
    container_name = data[0]
    func = data[1]
    name = data[2]
    description = data[3]
    in_params = data[4]
    out_params = data[5]
    container = container_classes[container_name]
    in_p = dict()
    in_p.update(container.in_params)
    in_p.update(in_params)
    out_p = out_params if out_params else dict()

    class SubmoduleWrapper(EventEmitter):
        in_params = in_p

        out_params = out_p

        def run(self, in_params_):
            validated = validate_params(in_p, in_params_)
            if validated:
                c = container(validated)
                return func(c, validated)

    SubmoduleWrapper.name = name
    SubmoduleWrapper.version = container.version
    SubmoduleWrapper.description = description
    SubmoduleWrapper.author = container.author
    register_module(SubmoduleWrapper,
                    container_name + "/" + name)

def submodule(*, name, description, in_params, out_params=None):
    def decorator(func):
        submodule_methods.append(
            [func.__module__.replace(".", "/"), func, name, description,
             in_params, out_params])

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class ISFModule:

    def __init__(self, *, name, version="1.0", description=None,
                 author=None):
        if state != State.LOADING_MODULES:
            raise InvalidStateException(("Can only load modules while in %s " +
                                         "state (current state is %s)") % (
                                            State.LOADING_MODULES.name,
                                            state.name))
        self.name = name
        self.version = version
        self.description = description
        self.author = author

    def __call__(self, cls):
        if cls.__module__.startswith("modules"):
            raise ModuleLoadingException(
                "DO NOT IMPORT ISF MODULES DIRECTLY " +
                "- USE self.get_module_instance(name) INSTEAD")
        if not hasattr(cls, "run") or not callable(cls.run):
            raise ModuleLoadingException(
                ("Module '%s' does not " +
                 "provide the obligatory 'run' method") % self.name)
        if not hasattr(cls, "in_params") or not isinstance(
                cls.in_params, dict):
            raise ModuleLoadingException(("Module '%s' does not " +
                                          "provide input parameters list")
                                         % self.name)

        if hasattr(cls, "out_params") and not isinstance(
                cls.out_params, dict):
            raise ModuleLoadingException(("Module '%s' does not "
                                          + "provide output parameters list")
                                         % self.name)

        class ModuleWrapper(cls, EventEmitter):
            name = self.name
            version = self.version
            description = self.description
            author = self.author

            def __init__(self, *args, **kwargs):
                self.get_module_instance = get_module_instance
                super(ModuleWrapper, self).__init__(*args, **kwargs)

            def run(self, params):
                validated = validate_params(
                    super(ModuleWrapper, self).in_params, params)
                if validated:
                    out = super(ModuleWrapper, self).run(validated)
                    return out if out else dict()

        register_module(ModuleWrapper, cls.__module__.replace(".", "/"))
        return ModuleWrapper


class ISFGui:

    def __init__(self, *, module_name):
        if state != State.LOADING_GUI:
            raise InvalidStateException(("Can only load modules while in %s " +
                                         "state (current state is %s)") % (
                                            State.LOADING_GUI.name, state.name))
        self.module_name = module_name

    def __call__(self, cls):

        if self.module_name not in loaded_modules:
            raise NoSuchModuleException("No module named %s" % self.module_name)

        class GuiWrapper(cls):
            module_name = self.module_name

        register_gui(GuiWrapper, self.module_name)
        return GuiWrapper


module_in_params = dict()

loaded_modules = dict()
loaded_gui_classes = dict()
curr_module = None
console_mode = False

state = State.LOADING_MODULES


def error_message(msg):
    ISFConsole.console_message(msg, ISFConsole.LogLevel.ERROR)


def register_module(wrapper_cls, module_name):
    if module_name in loaded_modules:
        raise ModuleLoadingException(
            "Module %s is already loaded" % module_name)
    loaded_modules[module_name] = wrapper_cls


def register_gui(wrapper_cls, module_name):
    if module_name in loaded_gui_classes:
        raise GuiLoadingException(
            "GUI for module %s is already loaded" % module_name)
    loaded_gui_classes[module_name] = wrapper_cls


def validate_params(in_params, params):
    validated = dict()
    for p_name, p_desc in in_params.items():
        if p_name not in params:
            if p_desc.required and not p_desc.default_value:
                error_message("Missing required parameter %s" % p_name)
                return
            else:
                validated[p_name] = p_desc.default_value
        else:
            try:
                validated[p_name] = p_desc.value_type(params[p_name])
            except ValueError:
                error_message("Parameter %s has invalid type" % p_name)
                return
    return validated


def build_gui():
    pass


def start():
    global state, console_mode
    ISFConsole.console_message("Starting IoTSecFuzz Framework")
    ISFConsole.console_message("Fetching modules")
    commons.load_modules_from_directory("modules")
    register_submodules()
    ISFConsole.console_message(
        "Loaded %d modules" % len(list(loaded_modules.keys())),
        ISFConsole.LogLevel.FINE)
    if "--nogui" not in sys.argv:
        console_mode = True
        ISFConsole.console_message(
            "Console mode requested, skipping GUI initialization")
    else:
        state = State.LOADING_GUI
        ISFConsole.console_message("Loading GUI")
        commons.load_modules_from_directory("gui")
        ISFConsole.console_message(
            "Loaded %d GUI classes" % len(list(loaded_gui_classes.keys())),
            ISFConsole.LogLevel.FINE)
    state = State.READY
    if console_mode:
        ISFConsole.register_commands()
        ISFConsole.run_console()
    else:
        build_gui()
