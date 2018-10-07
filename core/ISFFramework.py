import sys
import pkgutil
from enum import Enum
from util.exceptions import *
from util.events import EventEmitter


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
        if not hasattr(cls, "in_params_def") or not isinstance(
                cls.in_params_def, dict):
            raise ModuleLoadingException(("Module '%s' does not " +
                                          "provide input parameters list")
                                         % self.name)

        if hasattr(cls, "out_params_def") and not isinstance(
                cls.out_params_def, dict):
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
                validated = validate_params(super(ModuleWrapper, self), params)
                if validated:
                    return super(ModuleWrapper, self).run(params)

        register_module(ModuleWrapper, cls)
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
module_out_params = dict()

loaded_modules = dict()
loaded_gui_classes = dict()
curr_module = None

state = State.LOADING_MODULES


def load_modules_from_directory(dir_name):
    for importer, package_name, is_pkg in pkgutil.walk_packages([dir_name]):
        if package_name not in sys.modules:
            importer.find_module(package_name).load_module(package_name)


def message(msg):
    print("[-] " + msg)


def register_module(wrapper_cls, module_cls):
    module_name = module_cls.__module__.replace(".", "/")
    if module_name in loaded_modules:
        raise ModuleLoadingException(
            "Module %s is already loaded" % module_name)
    loaded_modules[module_name] = wrapper_cls


def register_gui(wrapper_cls, module_name):
    if module_name in loaded_gui_classes:
        raise GuiLoadingException(
            "GUI for module %s is already loaded" % module_name)
    loaded_gui_classes[module_name] = wrapper_cls


def validate_params(isf_module, params):
    validated = dict()
    for p_name, p_desc in isf_module.in_params_def.items():
        if p_name not in params:
            if p_desc.required and not p_desc.default_value:
                message("Missing required parameter %s" % p_name)
                return
            else:
                validated[p_name] = p_desc.default_value
        else:
            try:
                validated[p_name] = p_desc.value_type(params[p_name])
            except TypeError:
                message("Parameter %s has invalid type" % p_name)
                return
    return params


def start():
    global state
    print("[*] Starting IoTSecFuzz Framework")
    print("[*] Fetching modules")
    load_modules_from_directory("modules")
    print("[+] Loaded %d modules" % len(list(loaded_modules.keys())))
    state = State.LOADING_GUI
    print("[*] Loading GUI")
    load_modules_from_directory("gui")
    print("[+] Loaded %d GUI classes" % len(list(loaded_gui_classes.keys())))
    print(loaded_modules)
    loaded_modules["firmware/golddigger"]().run({"TARGET": ""})
