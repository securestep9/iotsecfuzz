from tabulate import tabulate

import core.console.ISFConsole as ISFConsole
import core.ISFProfiles as ISFProfiles
import core.ISFFramework as ISFFramework


@ISFConsole.ISFConsoleCommand("presets",
                              description="Lists presets for current profile")
class CommandPresets:

    def run(self, args):
        if not ISFFramework.curr_profile:
            ISFConsole.console_message("No profile selected",
                                       ISFConsole.LogLevel.ERROR)
            return
        print(tabulate(
            [[n, m] for n, m in
             ISFFramework.curr_profile.presets.items()],
            headers=["Name", "Value"],
            tablefmt="psql"))
