from tabulate import tabulate

import core.console.ISFConsole as ISFConsole
import core.ISFFramework as ISFFramework


@ISFConsole.ISFConsoleCommand("search",
                              description="Finds module by name substring",
                              aliases=["find"])
class CommandSearch:

    def run(self, args):
        results = dict()
        if len(args) < 2:
            ISFConsole.console_message(
                "Usage: %s <string>" % (args[0] if args[0] else "search"))
            return
        query = " ".join(args[1:])
        for k, m in ISFFramework.loaded_modules.items():
            if query in k:
                results[k] = m
        if not len(results):
            ISFConsole.console_message("No results", ISFConsole.LogLevel.ERROR)
            return
        ISFConsole.console_message("Search results: ", ISFConsole.LogLevel.FINE)
        print(tabulate(
            [[n, m.version, m.author, m.description] for n, m in
             results.items()],
            headers=["Name", "Version", "Author", "Description"],
            tablefmt="psql"))
