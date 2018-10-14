from tabulate import tabulate

import core.console.ISFConsole as ISFConsole
import core.ISFFramework as ISFFramework


@ISFConsole.ISFConsoleCommand("list", description="Lists all loaded modules")
class CommandSearch:

    def run(self, args):
        ISFConsole.console_message("Loaded modules: ", ISFConsole.LogLevel.FINE)
        print(tabulate(
            [[n, m.version, m.author, m.description] for n, m in
             ISFFramework.loaded_modules.items()],
            headers=["Name", "Version", "Author", "Description"],
            tablefmt="psql"))
