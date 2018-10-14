import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole


@ISFConsole.ISFConsoleCommand("use",
                              description="Selects module to use",
                              params_desc=["module name"],
                              aliases=["select", "sel"])
class CommandUse:

    def run(self, args):
        if len(args) < 2:
            ISFConsole.console_message(
                "Usage: %s <module name>" % (args[0] if len(args) else "use"),
                ISFConsole.LogLevel.ERROR)
            return
        name = args[1]
        if name not in ISFFramework.loaded_modules:
            ISFConsole.console_message("No module named %s" % name,
                                       ISFConsole.LogLevel.ERROR)
            return
        ISFConsole.curr_module_name = name
        ISFFramework.curr_module = ISFFramework.loaded_modules[name]()
        module_in_params = dict()
        for p_name, p in ISFFramework.curr_module.in_params.items():
            if p.default_value:
                module_in_params[p_name] = p.default_value
