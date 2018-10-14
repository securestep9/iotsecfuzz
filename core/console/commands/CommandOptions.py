import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from tabulate import tabulate


@ISFConsole.ISFConsoleCommand("options",
                              description="Prints module in/out parameters",
                              aliases=["params"])
class CommandOptions:

    def run(self, args):
        if not ISFFramework.curr_module:
            ISFConsole.console_message("No module selected",
                                       ISFConsole.LogLevel.ERROR)
            return
        ISFConsole.console_message("Module input parameters:")
        print(tabulate([[n, (ISFFramework.module_in_params[
                                 n] if n in ISFFramework.module_in_params else
                             None),
                         p.value_type.__name__, p.required,
                         p.default_value, p.description] for n, p in
                        ISFFramework.curr_module.in_params.items()],
                       headers=["Name", "Current value", "Type", "Required",
                                "Default value",
                                "Description"],
                       tablefmt="psql"))
        if hasattr(ISFFramework.curr_module, "out_params"):
            ISFConsole.console_message("Module output parameters: ")
            print(tabulate([[n, p.description] for n, p in
                            ISFFramework.curr_module.out_params.items()],
                           headers=["Name", "Description"],
                           tablefmt="psql"))
