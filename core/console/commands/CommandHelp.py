from tabulate import tabulate

import core.console.ISFConsole as ISFConsole


@ISFConsole.ISFConsoleCommand("help", description="Displays help")
class CommandHelp:

    def run(self, args):
        print(tabulate([[cmd.command_name, ", ".join(
            cmd.params_desc) if cmd.params_desc else None,
                         cmd.description,
                         ", ".join(cmd.aliases) if cmd.aliases else None] for
                        cmd in
                        ISFConsole.command_classes],
                       headers=["Name", "Parameters", "Description", "Aliases"],
                       tablefmt="psql"))
