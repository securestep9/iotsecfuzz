from enum import Enum

from termcolor import cprint

import core.ISFFramework as ISFFramework
import util.commons as commons
from util.exceptions import InitializationException


class LogLevel(Enum):
    ALL = 0
    FINE = 1
    ERROR = 2


class ISFConsoleCommand:

    def __init__(self, command_name, *, description, params_desc=None,
                 aliases=None):
        self.command_name = command_name
        self.description = description
        self.params_desc = params_desc
        self.aliases = aliases

    def __call__(self, cls):
        if not hasattr(cls, "run") or not callable(cls.run):
            raise InitializationException(
                "Commands '%s' does not provide the 'run' method"
                % self.command_name)

        class CommandWrapper(cls):
            command_name = self.command_name
            description = self.description
            params_desc = self.params_desc
            aliases = self.aliases

        names = [self.command_name]
        if self.aliases:
            names.extend(self.aliases)
        register_command(CommandWrapper, names)
        return CommandWrapper


commands = dict()
command_classes = list()
curr_module_name = None


def register_commands():
    commons.load_modules_from_directory("core/console/commands")


def register_command(cls, names):
    cmd = cls()
    for command_name in names:
        if command_name in commands:
            raise InitializationException(
                "Command '%s' already registered" % command_name)
        commands[command_name] = cmd
    command_classes.append(cls)


def console_message(msg, level=LogLevel.ALL):
    prefix = ["*", "+", "-"]
    colors = ["cyan", "green", "red"]
    cprint("[%s] " % prefix[level.value], color=colors[level.value], end="")
    print(msg)


def run_console():
    global curr_module_name
    while True:
        print("ISFFramework ", end="")
        if ISFFramework.curr_module:
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
        elif cmd in commands:
            commands[cmd].run(user_input)
        else:
            console_message("Unknown command: %s" % cmd, LogLevel.ERROR)
