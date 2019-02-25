import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from tabulate import tabulate


@ISFConsole.ISFConsoleCommand("run",
                              description="Executes selected module",
                              aliases=["start"])
class CommandRun:

    def run(self, args):
        if not ISFFramework.curr_module:
            ISFConsole.console_message("No module selected",
                                       ISFConsole.LogLevel.ERROR)
        else:
            ISFConsole.console_message(
                "Running module '%s'..." % ISFConsole.curr_module_name)
            out = None
            try:
                out = ISFFramework.curr_module.run(
                    ISFFramework.module_in_params)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                ISFConsole.console_message(
                    "Error encountered while running module: %s" % str(e),
                    ISFConsole.LogLevel.ERROR)
            if out:
                ISFConsole.console_message("Module output:",
                                           ISFConsole.LogLevel.FINE)
                print(tabulate([[k, v] for k, v in out.items()],
                               headers=["Name", "Value"],
                               tablefmt="psql"))
