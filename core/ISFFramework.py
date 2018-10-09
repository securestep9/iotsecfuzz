import sys
import pkgutil
from enum import Enum
from util.exceptions import *
from util.events import EventEmitter
from termcolor import cprint
from tabulate import tabulate


class State(Enum):
    LOADING_MODULES = 0
    LOADING_GUI = 1
    READY = 2


class LogLevel(Enum):
    ALL = 0
    FINE = 1
    ERROR = 2


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
                validated = validate_params(super(ModuleWrapper, self), params)
                if validated:
                    out = super(ModuleWrapper, self).run(params)
                    return out if out else dict()

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

loaded_modules = dict()
loaded_gui_classes = dict()
curr_module = None
console_mode = False

state = State.LOADING_MODULES


def load_modules_from_directory(dir_name):
    for importer, package_name, is_pkg in pkgutil.walk_packages([dir_name]):
        if package_name not in sys.modules:
            importer.find_module(package_name).load_module(package_name)


def console_message(msg, level=LogLevel.ALL):
    prefix = ["*", "+", "-"]
    colors = ["cyan", "green", "red"]
    cprint("[%s] " % prefix[level.value], color=colors[level.value], end="")
    print(msg)


def error_message(msg):
    console_message(msg, LogLevel.ERROR)


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
    for p_name, p_desc in isf_module.in_params.items():
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
    return params


def build_gui():
    pass


def run_console():
    global curr_module, module_in_params
    curr_module_name = None
    while True:
        print("ISFFramework ", end="")
        if curr_module:
            print("(", end="")
            cprint(curr_module_name, color="yellow", end="")
            print(") ", end="")
        print("> ", end="")
        user_input = input().split()
        if not user_input:
            continue
        cmd = user_input[0].strip()
        if cmd == "exit" or cmd == "quit":
            break
        elif cmd == "use" or cmd == "select" or cmd == "sel":
            if len(user_input) < 2:
                console_message("Usage: %s <module name>" % cmd, LogLevel.ERROR)
                continue
            name = user_input[1]
            if name not in loaded_modules:
                console_message("No module named %s" % name, LogLevel.ERROR)
                continue
            curr_module_name = name
            curr_module = loaded_modules[name]()
            module_in_params = dict()
            for p_name, p in curr_module.in_params.items():
                if p.default_value:
                    module_in_params[p_name] = p.default_value
        elif cmd == "params" or cmd == "options":
            if not curr_module:
                console_message("No module selected", LogLevel.ERROR)
                continue
            console_message("Module input parameters:")
            print(tabulate([[n, p.value_type.__name__, p.required,
                             p.default_value, p.description] for n, p in
                            curr_module.in_params.items()],
                           headers=["Name", "Type", "Required", "Default value",
                                    "Description"],
                           tablefmt="psql"))
            if hasattr(curr_module, "out_params"):
                console_message("Module output parameters: ")
                print(tabulate([[n, p.description] for n, p in
                                curr_module.out_params.items()],
                               headers=["Name", "Description"],
                               tablefmt="psql"))
        elif cmd == "run" or cmd == "start":
            if not curr_module:
                console_message("No module selected", LogLevel.ERROR)
            else:
                console_message("Running module '%s'..." % curr_module_name)
                out = None
                try:
                    out = curr_module.run(module_in_params)
                except Exception as e:
                    error_message(
                        "Error encountered while running module: %s" % str(e))
                if out:
                    console_message("Module output:", LogLevel.FINE)
                    print(tabulate([[k, v] for k, v in out.items()],
                                   headers=["Name", "Value"],
                                   tablefmt="psql"))
        elif cmd == "set":
            if len(user_input) < 3:
                console_message("Usage: set <parameter name> <value>",
                                LogLevel.ERROR)
                continue
            if not curr_module:
                console_message("No module selected", LogLevel.ERROR)
                continue
            p_name = user_input[1]
            if p_name not in curr_module.in_params:
                console_message(
                    "Module '%s' does not require parameter '%s'" % (
                        curr_module_name, p_name), LogLevel.ERROR)
                continue
            p_value_str = " ".join(user_input).replace(cmd, "", 1)
            p_value_str = p_value_str.replace(p_name, "", 1).strip()
            p_type = curr_module.in_params[p_name].value_type
            p_value = None
            try:
                p_value = p_type(p_value_str)
            except ValueError:
                console_message("'%s' is not a valid value of type '%s'" % (
                    p_value_str, p_type.__name__), LogLevel.ERROR)
                continue
            module_in_params[p_name] = p_value
            console_message("%s ==> %s" % (p_name, p_value_str), LogLevel.FINE)
        elif cmd == "back":
            curr_module = None
            curr_module_name = None
            module_in_params = dict()
            continue
        elif cmd == "help":
            # use command
            cprint(" use <module name> ", color="cyan", end="")
            print("select module to work with")
            print("   aliases: ", end="")
            cprint("select, sel ", color="cyan")

            # options command
            cprint(" params ", color="cyan", end="")
            print("print module input/output parameters")
            print("   aliases: ", end="")
            cprint("options ", color="cyan")

            # set command
            cprint(" set <parameter name> <value> ", color="cyan", end="")
            print("set module input parameter value")

            # run command
            cprint(" run ", color="cyan", end="")
            print("execute selected module")
            print("   aliases: ", end="")
            cprint("start ", color="cyan")

            # back command
            cprint(" back ", color="cyan", end="")
            print("exit selected module")

            # help command
            cprint(" help ", color="cyan", end="")
            print("display help")

            # exit command
            cprint(" exit ", color="cyan", end="")
            print("shut down the framework")
            print("   aliases: ", end="")
            cprint("quit ", color="cyan")
        else:
            console_message("Unknown command: %s" % cmd, LogLevel.ERROR)


def start():
    global state, console_mode
    console_message("Starting IoTSecFuzz Framework")
    console_message("Fetching modules")
    load_modules_from_directory("modules")
    console_message("Loaded %d modules" % len(list(loaded_modules.keys())),
                    LogLevel.FINE)
    if "--nogui" not in sys.argv:
        console_mode = True
        console_message("Console mode requested, skipping GUI initialization")
    else:
        state = State.LOADING_GUI
        console_message("Loading GUI")
        load_modules_from_directory("gui")
        console_message(
            "Loaded %d GUI classes" % len(list(loaded_gui_classes.keys())),
            LogLevel.FINE)
    state = State.READY
    if console_mode:
        run_console()
    else:
        build_gui()
