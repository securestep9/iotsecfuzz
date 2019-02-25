import functools
import ast
import sys
from enum import Enum

import core.console.ISFConsole as ISFConsole
import core.ISFProfiles as ISFProfiles
import core.ISFGui as ISFGui
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


def get_module_class(name):
    return loaded_modules[name] if name in loaded_modules else None


def get_container_class(name):
    return container_classes[name] if name in container_classes else None


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

        # if cls.__module__.startswith("modules"):
        #     raise ModuleLoadingException(
        #         "DO NOT IMPORT ISF MODULES DIRECTLY " +
        #         "- USE self.get_module_instance(name) INSTEAD")

        class ContainerWrapper(cls, EventEmitter):
            version = self.version
            author = self.author

            def __init__(self, params):
                self.get_module = get_module_class
                self.get_container_class = get_container_class
                self._params = params
                super(ContainerWrapper, self).__init__(params)

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
    func._in_params = in_p
    out_p = out_params if out_params else dict()

    class SubmoduleWrapper(EventEmitter):
        in_params = in_p

        out_params = out_p

        def run(self, in_params_={}):
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
        def wrapper(self, params={}):
            validated = validate_params(func._in_params, params)
            if validated:
                return func(self, validated)  # func(*args, **kwargs)

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
      # if cls.__module__.startswith("modules"):
      #     raise ModuleLoadingException(
      #         "DO NOT IMPORT ISF MODULES DIRECTLY " +
      #         "- USE self.get_module_instance(name) INSTEAD")
        if not hasattr(cls, "run") or not callable(cls.run):
            raise ModuleLoadingException(
                ("Module '%s' does not " +
                 "provide the obligatory 'run' method") % self.name)
        if not hasattr(cls, "in_params") or not isinstance(
                cls.in_params, dict):
            raise ModuleLoadingException(("Module '%s' does not " +
                                          "provide input parameters list")
                                         % self.name)
        for pname, pvalue in cls.in_params.items():
            default_profile[cls.__module__.replace(".", "/") + ":" + pname] = \
                pvalue.default_value if pvalue.default_value else None
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
                self.get_module_class = get_module_class
                self.get_container_class = get_container_class
                super(ModuleWrapper, self).__init__(*args, **kwargs)

            def run(self, params={}):
                validated = validate_params(
                    super(ModuleWrapper, self).in_params, params)
                if validated:
                    out = super(ModuleWrapper, self).run(validated)
                    return out if out else dict()

        register_module(ModuleWrapper, cls.__module__.replace(".", "/"))
        return ModuleWrapper


module_in_params = dict()

loaded_modules = dict()
curr_module = None
curr_profile = None
console_mode = False

default_profile = dict()

state = State.LOADING_MODULES


def error_message(msg):
    if not console_mode:
        ISFGui.show_error_msg(msg)
    ISFConsole.console_message(msg, ISFConsole.LogLevel.ERROR)


def register_module(wrapper_cls, module_name):
    if module_name in loaded_modules:
        raise ModuleLoadingException(
            "Module %s is already loaded" % module_name)
    loaded_modules[module_name] = wrapper_cls


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
                if p_desc.value_type in (
                        int, float, list, dict, tuple, bool) \
                        and isinstance(params[p_name], str):
                    validated[p_name] = p_desc.value_type(
                        ast.literal_eval(params[p_name]))
                else:
                    validated[p_name] = p_desc.value_type(params[p_name])
            except ValueError:
                error_message("Parameter %s has invalid type" % p_name)
                return
    return validated


def build_gui():
    ISFGui.build_gui()


def use_profile(name):
    global curr_profile
    if name not in ISFProfiles.loaded_profiles:
        raise ProfileNotFoundException("Profile '%s' does not exist")
    curr_profile = ISFProfiles.loaded_profiles[name]
    for key, value in curr_profile.presets.items():
        module_name = key.split(":")[0]
        param_name = key.split(":")[1]
        if module_name not in loaded_modules:
            raise ModuleNotFoundError("No module named '%s'" % module_name)
        cls = loaded_modules[module_name]
        if param_name not in cls.in_params:
            ISFConsole.console_message(
                "Module %s does not have in parameter %s, skipping" % (
                    module_name, param_name), ISFConsole.LogLevel.ERROR)
        else:
            cls.in_params[param_name].default_value = value


def unset_profile():
    global curr_profile
    curr_profile = None
    for key, value in default_profile.items():
        module_name = key.split(":")[0]
        param_name = key.split(":")[1]
        loaded_modules[module_name].in_params[param_name].default_value = value


def start(user_mode=False):
    global state, console_mode
    ISFConsole.console_message("Starting IoTSecFuzz Framework")
    ISFConsole.console_message("Fetching modules")
    commons.load_modules_from_directory("modules")
    register_submodules()
    ISFConsole.console_message(
        "Loaded %d modules" % len(list(loaded_modules.keys())),
        ISFConsole.LogLevel.FINE)
    ISFConsole.console_message("Loading profiles")
    ISFProfiles.load_profiles()
    ISFConsole.console_message(
        "Loaded %d profiles" % len(list(ISFProfiles.loaded_profiles.keys())),
        ISFConsole.LogLevel.FINE)
    if "--nogui" in sys.argv or not user_mode:
        console_mode = True
        ISFConsole.console_message(
            "Console mode requested, skipping GUI initialization")
    else:
        state = State.LOADING_GUI
        ISFConsole.console_message("Loading GUI")
        build_gui()
    state = State.READY
    if console_mode and user_mode:
        ISFConsole.register_commands()
        ISFConsole.run_console()
